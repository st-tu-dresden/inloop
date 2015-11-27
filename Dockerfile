FROM java:7
RUN /bin/bash -c "export JAVA_HOME=$(readlink -f $(which java))"
ENV GRADLE_VERSION=2.5 \
    GRADLE_HOME=/opt/gradle \
    PATH=$PATH:${JAVA_HOME}/bin:${GRADLE_HOME}:${GRADLE_HOME}/bin
# install gradle
RUN /bin/bash -c "mkdir -p /tmp/gradle ${GRADLE_HOME} && cd /tmp/gradle && \
    wget -qO- -O gradle.zip https://services.gradle.org/distributions/gradle-${GRADLE_VERSION}-bin.zip && \
    unzip -qq gradle.zip && \
    mv ./gradle-${GRADLE_VERSION}/* ${GRADLE_HOME}/"
