# ffnvr - Distributed FFmpeg NVR

So me and my friend been working on our obscure video surveillance project. We wondered how do we approach the recording of hundreds of RTSP streams without thinking too much about hardware, cpu/memory/network load, etc.

**ffnvr** uses a kind of Redis Lock (see https://redis.io/glossary/redis-lock) to avoid race condition when distributing streams across replicas. This allows us to have leaderless replication.

Streams can be configured via AMQP (we use RabbitMQ) like this:

```
{
    "action": "<ADD | DELETE>",
    "guid": "<unique id, e.g. UUID4>",
    "name": "<also unique, used for naming output path>",
    "url": "<RTSP url>"
}
```

See [.env.example](.env.example) for startup configuration

As for storage, we currently use good ol' SMB/CIFS mount. Our future task is to introduce some kind of distributed storage in case we're out of network bandwidth and/or write speed of a single disk.

# License

idk
