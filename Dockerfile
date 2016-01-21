FROM java:8-jdk

RUN useradd -m -U gradle

RUN mkdir -p /home/gradle/exercises/
RUN mkdir -p /home/gradle/solution/
ADD media/exercises/ /home/gradle/exercises/
ADD run.sh /home/gradle/exercises/

VOLUME /home/gradle/solution/

RUN chown -R gradle:gradle /home/gradle/

USER gradle
WORKDIR /home/gradle/

RUN cd exercises && ./gradlew compileTestJava

ENTRYPOINT ["/bin/sh", "exercises/run.sh"]
CMD ["invalid-task"]
