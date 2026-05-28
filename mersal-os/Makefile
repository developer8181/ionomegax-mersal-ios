.PHONY: sync iso iso-docker test clean

sync:
	./build/sync-includes.sh

iso:
	sudo ./build/build-iso-debootstrap.sh

iso-docker:
	./build/build-iso-docker.sh

test:
	python3 -m unittest discover -s tests -v

clean:
	rm -rf build/live-work dist/*.iso dist/*.sha256 build/build.log
