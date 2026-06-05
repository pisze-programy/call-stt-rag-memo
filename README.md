## Overview
```
                [ USER ]
                   |
        [ Zadarma VoIP Gateway ]
          /                 \
  (DTMF 1: SAVE)        (DTMF 2: AUTH)
        /                     \
[FastAPI Webhook]             [ ]
       |                       |
 [OpenAI Whisper]             [ ]
       |                       |
   [pgvector]                 [ ]
```

### SAVE FLOW

```
+------------+      +-----------------+      +----------------+      +---------------+
| Call State | ---> | DTMF 1 Captured | ---> | Voice Recorded | ---> | Webhook Fired |
+------------+      +-----------------+      +----------------+      +---------------+
                                                                             |
+------------+      +-----------------+      +----------------+              |
|  pgvector  | <--- |  Embedding API  | <--- |  Whisper STT   | <------------+
+------------+      +-----------------+      +----------------+
```

### Envs
```
ZADARMA_KEY=
ZADARMA_SECRET=
ZADARMA_API_URL=
OPENAI_API_KEY=
KAFKA_BROKER=
MONGO_URI=
```