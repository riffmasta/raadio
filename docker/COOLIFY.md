# Coolify

Coolify eraldi ehitusrakendus ehitab ja testib selle repo Dockerfile'i ning
avaldab tõmmise privaatses registris. Salvesti rakendus tõmbab valitud tõmmise
ja käivitab ühe isikliku salvesti koos veebiliidesega. GitHub Actions kontrollib
koodi ja paigaldajaid; konteineritõmmist GitHubis ei ehitata ega avaldata.

## Register ja ehitamine

Registry teenus kasutab Coolify Docker Registry malli (`registry:3`),
genereeritud kasutajanime/parooli ning püsivat `registry-data` volume'it.
Privaatne HTTPS-aadress on `registry.riffman.eu`. Kohtvõrgu pöördproksi
lõpetab TLS-i ja edastab päringud registri HTTP-pordile, säilitades `Host`
ning määrates `X-Forwarded-Proto: https`. Luba mahukad voogedastusega
üleslaadimised ning piisav ajapiirang. Ära ava seda teenust ruuterist internetti.

Logi Coolify server Dockeriga registrisse (Servers → Registries), kasutades
Registry teenuse keskkonnamuutujates olevaid genereeritud andmeid. Need ei
käi reposse, ehitusargumentidesse ega vestlusesse.

Loo eraldi Git-põhine Compose application **Raadio image builder**:

- Repository ja branch: `https://github.com/riffmasta/raadio`, `main`.
- Compose location: `/compose.coolify.build.yaml`.
- Custom Build Command: `sh docker/build-image.sh`.
- Custom Start Command: `docker compose config --quiet`.
- Inject build arguments, preview deployments ja auto deploy: välja lülitatud.
- Ära lisa salvestuste/oleku volume'eid ega salvesti parooli.

Ehituskäsk käitab testid enne avaldamist. Tõmmised avaldatakse kujul
`registry.riffman.eu/raadio:<täispikk-commit>` ja mugavussildiga `main`.
Olemasolevat commit-silti ehituskäsk üle ei kirjuta. Ehitusrakendus ei
käivita püsivat konteinerit: selle runtime-olek võib seega olla `exited`,
kuigi ehituse deployment on `finished`.

Register ja ehitamine asuvad samas serveris salvestiga. Nende eraldamine
rakendusteks ei eralda CPU-, mälu- ega kettakasutust. Varunda registri volume
ning eemalda aegunud tõmmiseid läbimõeldult, jättes kasutatavad versioonid alles.

## Seadistus

Loo Git-põhine Application, build pack **Docker Compose**:

- Repository: `https://github.com/riffmasta/raadio`, branch `main`.
- Base directory: `/`, Compose location: `/compose.coolify.runtime.yaml`.
- `RAADIO_IMAGE`: valitud commit-sildiga või SHA256 digestiga registriaadress.
  Ära kasuta salvesti juurutuseks liikuvat `main` silti.
- Auto deploy ja preview deployments: välja lülitatud.
- Inject build arguments to Dockerfile: välja lülitatud. Runtime-seadeid
  pole ehitamiseks vaja; see hoiab ka Dockeri kihtide vahemälu kasutuses.
- Consistent container names: sisse lülitatud.
- `WEB_USER`: vaikimisi `raadio`.
- `SERVICE_PASSWORD_RAADIO`: Coolify genereeritud parool; vaata või muuda seda
  Coolify Environment Variables vaates. Ära lisa parooli reposse ega vestlusesse.
- `WEB_URL`: telefoni jaoks kasutatav HTTPS-aadress, ilma lõpu kaldkriipsuta.
- `WEB_BIND_ADDRESS`: hosti kohtvõrgu IP. Vaikimisi `127.0.0.1` lubab
  ligipääsu ainult serverist endast.

Sea `WEB_URL`, `WEB_BIND_ADDRESS` ja `SERVICE_PASSWORD_RAADIO` ainult
runtime-muutujateks, mitte build-time-muutujateks. `.dockerignore` välistab
Coolify loodud keskkonnafailid konteineritõmmisest.

Varasem `compose.coolify.yaml` jääb üherakendusega kohapealse ehituse
variandiks. Ehituse eraldamisel muuda olemasoleva salvesti Compose-faili
asukohta, säilitades rakenduse UUID, teenuse nime ning volume'id; ära loo
teist tootmise salvestit uute volume'itega.

Kohalikuks kasutamiseks sea `WEB_URL=http://<serveri-LAN-IP>:8788` ning
`WEB_BIND_ADDRESS=<serveri-LAN-IP>`. Hoia parool sisse lülitatud ning ära
suuna ruuterist seda porti internetti. Avalikku domeeni pole vaja.
HTTP kaudu saab MP3-faile salvestada, kuid telefoni offline-laadimine vajab
HTTPS-i. Hiljem saab Tailscale Serve'i suunata loopback pordile 8788 ning
seada `WEB_URL` vastavale privaatsele HTTPS-aadressile.

Salvestused ja rakenduse andmed (sh `config.json`, lukud ja podcasti võti)
asuvad `/recordings` volume'is. Salvesti `done.json`, tervisekontrolli ajatempel
ja protsessilukk asuvad eraldi `/state` volume'is. Mõlemad peavad säilima
konteineri uuesti loomisel. Failid kirjutab UID/GID 1000.

## Uuendamine

1. Vali ehitusrakenduses **Deploy** ning oota edukat ehitamist, teste ja push'i.
   See ei taaskäivita salvestit.
2. Kontrolli lehelt, et ühtegi salvestust pole pooleli. Sea salvesti rakenduses
   `RAADIO_IMAGE` edukalt ehitatud commitile või digestile ning vali **Deploy**.
   Coolify tõmbab tõmmise ja loob konteineri uuesti samade volume'itega.
3. Kontrolli, et konteiner on healthy, veebileht küsib parooli ja salvesti
   olek uueneb. Proovi lühikest salvestust ning helifailis edasi liikumist.

Salvesti jagatud faililukk takistab sama `/state` peal teist põhiprotsessi.
SIGTERM lõpetab pooleliolevad salvestused ja säilitab salvestatu enne väljumist;
see **ei oota saate lõpuni**. Konteiner annab selleks kuni 120 sekundit.
Deploy keset saadet võib seega saate lühemaks jätta; uuenda saadete vahel.
Tervisekontroll nõuab töötavat protsessi ja viimase 3 minuti edukat põhitsüklit.
Käivitumisele on kava laadimiseks antud 3 minutit.

Esimesel käivitusel saab Coolify terminalis kontrollida ligipääsu, õigusi,
salvestamist ja helifailis liikumist käsuga `python docker/smokecheck.py`.
See loob tühjas paigalduses ühe 20-sekundilise Vikerraadio testsalvestuse ja
märgib selle `/state/deployment-smoke.json` faili. Pärast konteineri uuesti
loomist sama käsku korrates kontrollitakse olemasoleva faili ja oleku säilimist.
Käsk ei salvesta kasutaja tellimuste kõrvale uut testi ega väljasta paroole.

## Taastamine ja varundus

- Varunda mõlemad volume'id ning Coolify keskkonnaseaded enda privaatsesse
  varunduskohta. Salvestused ja podcasti võti peavad jääma privaatseks.
- Eelmisele koodile naasmiseks sea `RAADIO_IMAGE` eelmisele edukale
  commit-sildile või digestile ning juuruta salvesti uuesti.
  Koodi tagasipööramine ei taasta volume'ite eelmist sisu.
- Ära kustuta rakendust koos volume'itega ega käivita `docker compose down -v`.
- ERR-i kava imporditakse endiselt kasutaja brauseris järjehoidjaga;
  Coolify ei lisa ERR-i kaitsemeetmetest mööduvat päringut.
