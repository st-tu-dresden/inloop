FROM java:7

RUN mkdir -p /mnt/checker/task/
VOLUME /mnt/solution/

# Add task repo to container and build gradlew deps
ADD media/exercises/ /mnt/checker/
RUN ./mnt/checker/gradlew
