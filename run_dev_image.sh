container_name="PyCTB_DEV"

# Remove any existing container with the specified name
docker rm $container_name

# Run the Docker container from the built image
docker run \
	--detach \
	--interactive \
	--name $container_name \
	--volume "/home/mohammadreza/Project/pyCryptoTraderBot":"/project"\
	py_ctb_dev_img \
	bash

