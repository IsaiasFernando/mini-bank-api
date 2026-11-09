from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from app.core.config import settings
from app.routers import auth, users, accounts, transfers
from app.services.exceptions import (
    BankingError, AccountNotFound, InsufficientFunds, InvalidAmount, SameAccount,
)

app = FastAPI(title=settings.app_name, version="1.0.2",
              description="API educacional de banco digital com autenticação JWT e operações bancárias.",
              docs_url="/docs", redoc_url="/redoc")
app.state.limiter = auth.limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(BankingError)
async def banking_error_handler(request: Request, exc: BankingError):
    """Converte erros esperados do domínio em respostas HTTP consistentes."""
    if isinstance(exc, AccountNotFound):
        status_code = 404
    elif isinstance(exc, (InsufficientFunds, InvalidAmount, SameAccount)):
        status_code = 422
    else:
        status_code = 400
    return JSONResponse(status_code=status_code, content={"detail": str(exc)})


# O último middleware adicionado fica mais externo: o CORS envolve o rate limit,
# então até as respostas 429 levam os cabeçalhos de CORS.
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins,
                   allow_credentials=True, allow_methods=["GET", "POST"],
                   allow_headers=["Authorization", "Content-Type"])


@app.get("/health", tags=["Saúde"])
def health():
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(accounts.router)
app.include_router(transfers.router)
