from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# URL para crear la base de datos local SQLite en la raíz de backend
SQLALCHEMY_DATABASE_URL = "sqlite:///./expensr.db"

# Creación del motor de base de datos
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Creador de sesiones de base de datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Clase base de la que heredarán nuestros modelos ORM
Base = declarative_base()


# Inyector de dependencia para abrir y cerrar sesión en cada petición HTTP
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
