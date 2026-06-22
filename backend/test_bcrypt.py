from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
try:
    h = pwd_context.hash("admin")
    print("Hash success:", h)
    v = pwd_context.verify("admin", h)
    print("Verify success:", v)
except Exception as e:
    import traceback
    traceback.print_exc()
