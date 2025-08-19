# מדריך טכני: ארכיטטורת קוד הפייתון

מסמך זה מספק ניתוח טכני, קובץ אחר קובץ ושורה אחר שורה, של אפליקציית ה-FastAPI. המטרה היא להסביר את תפקידו של כל רכיב, את זרימת הנתונים, ואת ההיגיון מאחורי מבנה הקוד.

## ארכיטטורה כללית

האפליקציה בנויה בארכיטטורה מודולרית כדי להבטיח הפרדת אחריויות (Separation of Concerns). הזרימה הכללית היא:

`main.py` (נקודת כניסה) -> `crud/items.py` (שכבת API) -> `dependencies.py` (יוצר את ה-DAL) -> `dal.py` (שכבת גישה לנתונים)

---

### 1. `dependencies.py` - מרכז התצורה והתלויות

קובץ זה הוא הראשון שמתבצע בפועל, ותפקידו להכין את הרכיבים המשותפים לאפליקציה.

```python
# שורה 1-2: מייבאים את הכלים הדרושים. 'os' לקריאת משתני סביבה,
# ו-'DataLoader' מקובץ ה-dal שלנו.
import os
from .dal import DataLoader

# שורות 6-12: איסוף התצורה.
# כל פרמטר נדרש נקרא ממשתנה סביבה באמצעות os.getenv().
# אם המשתנה לא קיים (למשל, בריצה מקומית), ניתן ערך ברירת מחדל.
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = int(os.getenv("MONGO_PORT", 27017))
MONGO_USER = os.getenv("MONGO_USER", "")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD", "")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "mydatabase")
MONGO_COLLECTION_NAME = os.getenv("MONGO_COLLECTION_NAME", "data")

# שורות 15-20: בניית מחרוזת החיבור (Connection String URI).
# הקוד בודק אם סופקו שם משתמש וסיסמה.
# אם כן, הוא בונה URI עם אימות (שמתאים ל-OpenShift).
# אם לא, הוא בונה URI פשוט (שמתאים ל-MongoDB מקומי ללא אימות).
if MONGO_USER and MONGO_PASSWORD:
    MONGO_URI = f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/?authSource=admin"
else:
    MONGO_URI = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/"

# שורות 24-27: יצירת מופע יחיד (Singleton) של ה-DataLoader.
# השורה הזו רצה פעם אחת בלבד כשהאפליקציה עולה.
# אנחנו "מזריקים" (inject) את התצורה שאספנו לקלאס ה-DataLoader.
# המשתנה 'data_loader' מיובא לאחר מכן בכל מקום שצריך גישה ל-DB.
data_loader = DataLoader(
    mongo_uri=MONGO_URI, db_name=MONGO_DB_NAME, collection_name=MONGO_COLLECTION_NAME
)
```

---

### 2. `dal.py` - שכבת הגישה לנתונים (DAL)

קובץ זה מכיל את כל הלוגיקה של התקשורת עם MongoDB. הוא לא יודע כלום על HTTP או FastAPI.

```python
# ... (ייבואים של pymongo ו-typing)

# שורה 12: הגדרת הקלאס DataLoader.
class DataLoader:
    # שורה 19: הבנאי (__init__) מקבל את התצורה שהוזרקה מ-dependencies.py.
    # הוא מאתחל את כל התכונות של האובייקט ל-None. הן יקבלו ערך רק לאחר חיבור מוצלח.
    def __init__(self, mongo_uri: str, db_name: str, collection_name: str):
        self.mongo_uri = mongo_uri
        self.db_name = db_name
        self.collection_name = collection_name
        self.client: Optional[AsyncMongoClient] = None
        self.db: Optional[Database] = None
        self.collection: Optional[Collection] = None

    # שורה 27: מתודת החיבור. 'async' כי היא מבצעת פעולות רשת.
    async def connect(self):
        try:
            # שורה 31: יוצר את הלקוח הא-סינכרוני עם timeout.
            self.client = AsyncMongoClient(self.mongo_uri, serverSelectionTimeoutMS=5000)
            # שורה 33: 'await' שולח פקודת 'ping' ומחכה לתשובה כדי לוודא שהחיבור תקין.
            await self.client.admin.command("ping")
            # שורות 34-35: מקבלים גישה לאובייקט ה-database וה-collection.
            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]
            # שורות 37-38: מפעילים את המתודות להגדרת אינדקסים ואתחול נתונים.
            await self._setup_indexes()
            await self._initialize_data()
        except PyMongoError as e:
            # במקרה של כשל, מאפסים את כל המשתנים ומודיעים על שגיאה.
            self.client = None; self.db = None; self.collection = None

    # שורות 63-66 (get_all_data):
    # שורה 65: בדיקה קריטית - אם החיבור נכשל, self.collection יהיה None.
    # במקרה כזה, זורקים שגיאה כדי ששכבת ה-API תדע שהפעולה נכשלה.
    if self.collection is None: raise RuntimeError("Database connection is not available.")
    # שורה 69: 'async for' היא לולאה א-סינכרונית ש"מושכת" מסמכים מה-DB אחד-אחד.
    async for item in self.collection.find({}):
        # שורה 70: המרת ה-_id (אובייקט ObjectId) למחרוזת (str) תואמת-JSON.
        item["_id"] = str(item["_id"])
        items.append(item)
    
    # (הסבר דומה חל על שאר מתודות ה-CRUD, המשתמשות בפונקציות כמו find_one, insert_one, וכו')
```

---

### 3. `models.py` - מודלי הנתונים (הסכמה)

קובץ זה מגדיר את "צורות" הנתונים באמצעות Pydantic. הוא משמש כ"חוזה" עבור ה-API.

```python
from pantic import BaseModel, Field

# שורה 7: 'PyObjectId = str' הוא כינוי סוג (Type Alias).
# הוא עוזר לנו לזכור שבקוד, ה-ID של מונגו הוא מסוג str.
PyObjectId = str

# שורה 15: ItemBase מגדיר את השדות המשותפים לכל הפריטים.
class ItemBase(BaseModel):
    first_name: str
    last_name: str

# שורה 23: ItemCreate יורש מ-ItemBase ומוסיף שדה.
# הוא משמש לוולידציה של קלט בבקשות ליצירת פריט.
class ItemCreate(ItemBase):
    ID: int

# שורה 43: ItemInDB הוא המודל המלא, המייצג פריט שחוזר מה-DB.
class ItemInDB(ItemBase):
    # שורה 51: 'id: PyObjectId = Field(alias='_id')' הוא החלק המרכזי.
    # 'alias' אומר ל-Pydantic: בנתונים הנכנסים חפש '_id', וב-JSON היוצא צור 'id'.
    id: PyObjectId = Field(alias='_id')
    ID: int

    # שורה 54: 'class Config' מאפשרת התנהגות מיוחדת.
    # 'populate_by_name = True' מאפשר ל-alias לעבוד בשני הכיוונים.
    class Config:
        populate_by_name = True
```

---

### 4. `crud/items.py` - שכבת ה-API (הראוטר)

קובץ זה מגדיר את נקודות הקצה של ה-API ומכיל את לוגיקת ה-HTTP.

```python
from fastapi import APIRouter, HTTPException, status

# ... (ייבואים נוספים)

# שורה 10: יוצרים APIRouter.
# 'prefix' קובע שכל הכתובות כאן יתחילו ב-/items.
# 'tags' מארגן את נקודות הקצה בתיעוד ה-Swagger.
router = APIRouter(prefix="/items", tags=["Items CRUD"])


# שורה 17: הדקורטור @router.post מגדיר נקודת קצה.
# 'response_model' אומר ל-FastAPI מה יהיה מבנה התשובה המוצלחת.
# 'status_code' קובע את קוד ה-HTTP שיוחזר בהצלחה.
@router.post("/", response_model=models.SoldierInDB, status_code=status.HTTP_201_CREATED)
async def create_item(item: models.SoldierCreate):
    # 'item: models.ItemCreate' מבצע ולידציה אוטומטית על גוף הבקשה.
    try:
        # קוראים למתודה המתאימה ב-DAL.
        created_item = await data_loader.create_soldier(item)
        return created_item
    except ValueError as e:
        # תופסים שגיאת 'ID כפול' מה-DAL והופכים אותה לשגיאת HTTP 409.
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    # ... (טיפול בשגיאות נוספות)
```

---

### 5. `main.py` - הרכבת האפליקציה

הקובץ הראשי שמחבר את כל החלקים.

```python
# ... (ייבואים)

# שורה 12: 'lifespan' היא פונקציה מיוחדת ש-FastAPI מריץ.
# הקוד לפני 'yield' רץ בעליית השרת (כאן אנו מתחברים ל-DB).
# הקוד אחרי 'yield' רץ בכיבוי השרת (כאן אנו מתנתקים).
@asynccontextmanager
async def lifespan(app: FastAPI):
    await data_loader.connect()
    yield
    data_loader.disconnect()

# שורה 24: יוצרים את אפליקציית FastAPI ומעבירים לה את ה-lifespan.
app = FastAPI(lifespan=lifespan, ...)

# שורה 30: ★★★ החיבור המרכזי ★★★
# פקודה זו "מחברת" את כל נקודות הקצה שהוגדרו ב-items.py לאפליקציה הראשית.
app.include_router(items.router)

# שורות 34, 63: מגדירים נקודות קצה נוספות ('/data' המקורית ו-'/' לבדיקת בריאות)
# ששייכות ישירות לאפליקציה הראשית.
@app.get("/data", ...)
# ...
```