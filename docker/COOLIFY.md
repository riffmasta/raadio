# Coolify

Coolify ehitab selle repo Dockerfile'i serveris ja käivitab ühe isikliku
salvesti koos veebiliidesega. GitHub Actions kontrollib koodi ja paigaldajaid;
konteineritõmmist GitHubis ei ehitata ega avaldata.

## Seadistus

Loo Git-põhine Application, build pack **Docker Compose**:

- Repository: `https://github.com/riffmasta/raadio`, branch `main`.
- Base directory: `/`, Compose location: `/compose.coolify.yaml`.
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

1. Kontrolli lehelt, et ühtegi salvestust pole pooleli ning järgmise alguseni
   on ehituseks ja taaskäivituseks piisavalt aega.
2. Ava Coolify rakendus ja vali **Deploy**. Coolify võtab `main` haru koodi,
   ehitab Dockerfile'i serveris ning loob konteineri uuesti samade volume'itega.
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
- Eelmisele koodile naasmiseks juuruta Coolifyst eelmine edukas commit uuesti.
  Koodi tagasipööramine ei taasta volume'ite eelmist sisu.
- Ära kustuta rakendust koos volume'itega ega käivita `docker compose down -v`.
- ERR-i kava imporditakse endiselt kasutaja brauseris järjehoidjaga;
  Coolify ei lisa ERR-i kaitsemeetmetest mööduvat päringut.
