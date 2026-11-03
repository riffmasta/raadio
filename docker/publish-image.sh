#!/bin/sh
# Called after Coolify's Compose build, inside its deployment helper.
set -eu

# At the start phase Coolify has written .env, including SOURCE_COMMIT.
# Reading the resolved Compose image avoids depending on .git (removed by Coolify).
image=$(docker compose -f compose.coolify.build.yaml config --images)
image_repository=${image%:*}
revision=${image##*:}
case "$revision" in
    ""|*[!0-9a-f]*) echo "Expected a full Git commit image tag" >&2; exit 1 ;;
esac
test "${#revision}" -eq 40

if docker manifest inspect "$image" >/dev/null 2>&1; then
    echo "Already published: $image"
    # Reuse the published commit image, even if the build used newer base layers.
    docker pull "$image"
else
    # No radio streams, production configuration, or recording volumes are used.
    for test in recorder/tests/test_core.py recorder/tests/test_runtime.py; do
        docker run --rm --network none --read-only \
            --cap-drop ALL --security-opt no-new-privileges:true \
            --tmpfs /tmp:mode=1777 \
            --entrypoint python "$image" "$test"
    done

    docker push "$image"
fi

for alias in main latest; do
    docker tag "$image" "$image_repository:$alias"
    docker push "$image_repository:$alias"
done
echo "Ready to deploy: $image"
