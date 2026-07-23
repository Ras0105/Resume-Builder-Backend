Read It Like a Real Request

Once you've gone through the files once, revisit them by tracing a single user action. This reinforces how the pieces fit together:

User opens website
        │
        ▼
index.html
        │
        ▼
script.js
        │
        ▼
POST /api/create-order
        │
        ▼
main.py
        │
        ▼
orders.py
        │
        ▼
payment.py
        │
        ▼
database.py + models.py
        │
        ▼
Razorpay
        │
        ▼
webhooks.py
        │
        ▼
Verify payment
        │
        ▼
pdf_generator.py
        │
        ▼
resume_template.html
        │
        ▼
storage.py
        │
        ▼
email.py
        │
        ▼
downloads.py
        │
        ▼
User downloads the resume






The Complete Reading Order

1. main.py
2. config.py
3. database.py
4. models.py
5. schemas.py

6. routers/orders.py
7. routers/webhooks.py
8. routers/downloads.py

9. services/payment.py
10. services/pdf_generator.py
11. services/storage.py
12. services/email.py

13. templates/resume_template.html

14. frontend/index.html
15. frontend/script.js
16. frontend/styles.css
17. frontend/vercel.json