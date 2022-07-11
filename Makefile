UNAME_M := $(shell uname -m)
UNAME = $(shell uname)
IMAGE_NAME = call-report-data-collector

.PHONY = default


all: check-windows check-nix build

check-windows:

ifdef $(OS)
	@echo "❌ This script is intended to be run on a Linux or MacOS system. Please see the README.md file for more information."
	exit 1
else
	@echo "✅ This makefile is probably running on a Linux or MacOS system."
	@echo "👁️  Detecting OS and architecture..."
endif 

check-nix:

ifeq ($(UNAME),Linux)
	@echo "🐧 Running Linux"
else  ifeq ($(UNAME),Darwin)
	@echo "🍏 Running MacOS"
endif


ifeq ($(UNAME_M),x86_64)
	@echo "💻 Running on x86_64"
ARCH := amd64
else ifeq ($(UNAME_M),amd64)
	@echo "💻 Running on amd64"
ARCH := amd64
else ifeq ($(UNAME_M),aarch64)
	@echo "💻 Running on aarch64"
ARCH := arm64
else ifeq ($(UNAME_M),arm64)
	@echo "💻 Running on aarch64"
ARCH := arm64
else ifeq ($(UNAME_M),arm64v8)
	@echo "💻 Running on arm64v8"
ARCH := arm64
else
	@echo "❌ Platform is not amd64, x86_64, arm64, arm64v8 or aarch64. Please see the README.md file for more information."
	exit 1
endif

.PHONY = build

build:
	@echo "🚀 Building image for $(UNAME_M)"
	docker build --platform=$(ARCH) . -t $(IMAGE_NAME) 

server:
	@echo "🚀 Testing image for $(UNAME_M)"
	docker run --rm -it --entrypoint /bin/bash -v $(PWD)/code:/code -p 8080:8080 $(IMAGE_NAME)