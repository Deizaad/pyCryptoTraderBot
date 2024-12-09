#!/bin/bash

image_name="py_ctb_dev_img"

# remove any existing docker image with given image_name
docker rmi --force $image_name

# Build the Docker image
docker build --file "Dockerfile.dev" --tag $image_name .

# Optionally, tag and push the image
# docker tag my-image:latest your-registry/my-image:latest
# docker push your-registry/my-image:latest

