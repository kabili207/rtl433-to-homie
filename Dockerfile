FROM python:3.6-alpine
LABEL maintainer="Amy Nagle <kabi-git@openmuffin.com>"

RUN apk add --no-cache libusb git build-base cmake libusb-dev \
    && cd /tmp \
    && git clone git://git.osmocom.org/rtl-sdr.git \
    && mkdir rtl-sdr/build \
    && cd rtl-sdr/build \
    && cmake .. -DINSTALL_UDEV_RULES=ON -DDETACH_KERNEL_DRIVER=ON \
    && make \
    && make install \
    && git clone https://github.com/merbanan/rtl_433.git \
    && mkdir rtl_433/build \
    && cd rtl_433/build \
    && cmake .. \
    && make \
    && make install \
    && cd \
    && pip install --upgrade pip \
    && pip install paho-mqtt \
    && rm -rf /.wh /root/.cache /var/cache /tmp

COPY . .

CMD ["/bin/sh", "/entrypoint.sh"]
