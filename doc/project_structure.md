resume-builder/
├── frontend/                      # existing static app, deployed to Vercel
│   ├── index.html
│   ├── script.js
│   ├── styles.css (if split out)
│   └── vercel.json                # rewrites/env for API base URL
│
└── backend/                       # FastAPI service, deployed to Railway/Render/Fly
    ├── app/
    │   ├── main.py                 # FastAPI app, mounts routers, CORS config
    │   ├── config.py               # env vars (DB url, Razorpay keys, email keys)
    │   ├── database.py             # SQLAlchemy engine/session
    │   ├── models.py               # Order, ResumeData tables
    │   ├── schemas.py              # Pydantic request/response models
    │   │
    │   ├── routers/
    │   │   ├── orders.py            # POST /api/create-order
    │   │   ├── webhooks.py          # POST /api/webhook/razorpay
    │   │   └── downloads.py         # GET /api/download/{token} (signed link)
    │   │
    │   ├── services/
    │   │   ├── payment.py           # Razorpay client + signature verification
    │   │   ├── pdf_generator.py     # HTML → PDF (Playwright/WeasyPrint)
    │   │   ├── storage.py           # upload PDF, generate signed URL
    │   │   └── email.py             # send PDF link via Resend/SendGrid
    │   │
    │   └── templates/
    │       └── resume_template.html # server-side HTML template PDF is rendered from
    │
    ├── requirements.txt
    ├── .env.example
    └── Dockerfile                  # for Railway/Render/Fly deploy