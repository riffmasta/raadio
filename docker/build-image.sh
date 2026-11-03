#!/bin/sh
# Called by Coolify's builder application, inside its deployment helper.
set -eu

image_repository=${RAADIO_IMAGE_REPOSITORY:-registry.riffman.eu/raadio}
revision=$(git rev-parse HEAD)
image="$image_repository:$revision"

if docker manifest inspect "$image" >/dev/null 2>&1; then
    echo "Already published: $image"
    exit 0
fi

docker build \
    --label org.opencontainers.image.source=https://github.com/riffmasta/raadio \
    --label "org.opencontainers.image.revision=$revision" \
    --tag "$image" .

# No radio streams, production configuration, or recording volumes are used.
for test in recorder/tests/test_core.py recorder/tests/test_runtime.py; do
    docker run --rm --network none --read-only \
        --cap-drop ALL --security-opt no-new-privileges:true \
        --tmpfs /tmp:mode=1777 \
        --entrypoint python "$image" "$test"
done

docker push "$image"
docker tag "$image" "$image_repository:main"
docker push "$image_repository:main"
echo "Ready to deploy: $image"
