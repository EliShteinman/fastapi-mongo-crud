# מדריך טכני: ארכיטטורת קוד הפייתון

מסמך זה מספק ניתוח טכני, קובץ אחר קובץ ושורה אחר שורה, של אפליקציית ה-FastAPI לניהול נתוני חיילים. המטרה היא להסביר את תפקידו של כל רכיב, את זרימת הנתונים, ואת ההיגיון מאחורי מבנה הקוד.

## ארכיטטורה כללית

האפליקציה בנויה בארכיטטורה מודולרית כדי להבטיח הפרדת אחריויות (Separation of Concerns). הזרימה הכללית היא:

`main.py` (נקודת כניסה) → `crud/soldiers.py` (שכבת API) → `dependencies.py` (יוצר את ה-DAL) → `dal.py` (שכבת גישה לנתונים)

## מבנה הקבצים
```
data_loader/
├── crud/
│   └── soldiers.py    # נקודות קצה של ה-API
├── dal.py            # שכבת גישה לנתונים
├── dependencies.py   # ניהול תצורה ויצירת התלויות
├── main.py          # נקודת כניסה ראשית
└── models.py        # מודלי נתונים (Pydantic)
```

---

## 1. `dependencies.py` - מרכז התצורה והתלויות

קובץ זה הוא הראשון שמתבצע בפועל, ותפקידו להכין את הרכיבים המשותפים לאפליקציה.

```python
# שורות 1-2: מייבאים את הכלים הדרושים. 
# 'os' לקריאת משתני סביבה, ו-'DataLoader' מקובץ ה-dal שלנו.
import os
from .dal import DataLoader

# שורות 7-12: איסוף התצורה מסביבת ההפעלה.
# כל פרמטר נקרא ממשתנה סביבה באמצעות os.getenv().
# אם המשתנה לא קיים (למשל, בריצה מקומית), ניתן ערך ברירת מחדל.
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")           # כתובת השרת
MONGO_PORT = int(os.getenv("MONGO_PORT", 27017))           # פורט (הופך למספר)
MONGO_USER = os.getenv("MONGO_USER", "")                   # שם משתמש (ריק אם לא מוגדר)
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD", "")           # סיסמה (ריקה אם לא מוגדרת)
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "mydatabase")   # שם מסד הנתונים
MONGO_COLLECTION_NAME = os.getenv("MONGO_COLLECTION_NAME", "data")  # שם הקולקשן

# שורות 17-20: בניית מחרוזת החיבור (Connection String URI).
# הקוד בודק אם סופקו שם משתמש וסיסמה.
# אם כן - בונה URI עם אימות (מתאים ל-OpenShift עם credentials)
# אם לא - בונה URI פשוט (מתאים ל-MongoDB מקומי ללא אימות)
if MONGO_USER and MONGO_PASSWORD:
    MONGO_URI = f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/?authSource=admin"
else:
    MONGO_URI = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/"

# שורות 24-26: ★ יצירת מופע יחיד (Singleton) של ה-DataLoader ★
# השורה הזו רצה פעם אחת בלבד כשהאפליקציה עולה.
# אנחנו "מזריקים" (inject) את התצורה שאספנו לקלאס ה-DataLoader.
# המשתנה 'data_loader' מיובא לאחר מכן בכל מקום שצריך גישה למסד הנתונים.
data_loader = DataLoader(
    mongo_uri=MONGO_URI, 
    db_name=MONGO_DB_NAME, 
    collection_name=MONGO_COLLECTION_NAME
)
```

---

## 2. `models.py` - מודלי הנתונים (סכמה)

קובץ זה מגדיר את "צורות" הנתונים באמצעות Pydantic. הוא משמש כ"חוזה" עבור ה-API.

```python
# שורה 8: 'PyObjectId = str' הוא כינוי סוג (Type Alias).
# הוא עוזר לנו לזכור שבקוד, ה-ObjectId של מונגו מטופל כמחרוזת.
PyObjectId = str

# שורות 16-25: SoldierBase מגדיר את השדות הבסיסיים המשותפים לכל החיילים.
# כל חייל חייב לכלול: שם פרטי, משפחה, טלפון ודרגה.
class SoldierBase(BaseModel):
    first_name: str      # שם פרטי
    last_name: str       # שם משפחה  
    phone_number: int    # מספר טלפון
    rank: str           # דרגה צבאית

# שורות 28-34: SoldierCreate יורש מ-SoldierBase ומוסיף שדה ID.
# מודל זה משמש לוולידציה של קלט בבקשות ליצירת חייל חדש (POST).
class SoldierCreate(SoldierBase):
    ID: int             # מזהה חייל יחודי (מספר שלם)

# שורות 37-46: SoldierUpdate מאפשר עדכון חלקי של נתוני חייל.
# כל השדות אופציונליים - ניתן לעדכן חלק מהנתונים בלבד.
class SoldierUpdate(BaseModel):
    first_name: Optional[str] = None     # שם פרטי (אופציונלי)
    last_name: Optional[str] = None      # שם משפחה (אופציונלי)
    phone_number: Optional[int] = None   # מספר טלפון (אופציונלי)
    rank: Optional[str] = None          # דרגה (אופציונלית)

# שורות 49-64: SoldierInDB הוא המודל המלא לחייל שחוזר ממסד הנתונים.
class SoldierInDB(SoldierBase):
    # שורה 58: ★ החלק הקריטי ★ 
    # 'id: PyObjectId = Field(alias="_id")' יוצר מיפוי בין שדות:
    # בנתונים הנכנסים מ-MongoDB חפש '_id', וב-JSON היוצא צור שדה 'id'
    id: PyObjectId = Field(alias="_id")  # MongoDB ObjectId כמחרוזת
    ID: int                              # המזהה הנומרי שלנו

    class Config:
        # שורה 64: מאפשר יצירת מודל מאובייקטים (לא רק ממילונים)
        from_attributes = True
        # שורה 67: מאפשר ל-alias לעבוד בשני הכיוונים (_id ↔ id)
        populate_by_name = True
```

---

## 3. `dal.py` - שכבת הגישה לנתונים (Data Access Layer)

קובץ זה מכיל את כל הלוגיקה של התקשורת עם MongoDB. הוא לא יודע כלום על HTTP או FastAPI.

```python
# שורות 4-10: ייבוא כל הכלים הדרושים למונגו ולטיפול בנתונים
from bson import ObjectId                    # לטיפול ב-ObjectId של מונגו
from pymongo import AsyncMongoClient         # הלקוח הא-סינכרוני
from pymongo.errors import DuplicateKeyError, PyMongoError  # טיפול בשגיאות
from .models import SoldierCreate, SoldierUpdate           # המודלים שלנו

# שורות 13-26: הגדרת קלאס DataLoader - המומחה שלנו למונגו
class DataLoader:
    def __init__(self, mongo_uri: str, db_name: str, collection_name: str):
        # שמירת פרטי החיבור שהתקבלו מ-dependencies.py
        self.mongo_uri = mongo_uri
        self.db_name = db_name  
        self.collection_name = collection_name
        # אתחול כל החיבורים ל-None - יקבלו ערך רק אחרי חיבור מוצלח
        self.client: Optional[AsyncMongoClient] = None
        self.db: Optional[Database] = None
        self.collection: Optional[Collection] = None

# שורות 28-44: מתודת החיבור - הלב של המערכת
async def connect(self):
    try:
        # שורות 31-32: יצירת חיבור עם timeout של 5 שניות
        self.client = AsyncMongoClient(self.mongo_uri, serverSelectionTimeoutMS=5000)
        # שורה 34: שליחת 'ping' לוודא שהחיבור תקין (await = המתנה לתשובה)
        await self.client.admin.command("ping")
        # שורות 35-36: קבלת גישה למסד הנתונים ולקולקשן
        self.db = self.client[self.db_name]
        self.collection = self.db[self.collection_name]
        # שורה 38: הקמת אינדקס ייחודי על שדה ה-ID
        await self._setup_indexes()
    except PyMongoError as e:
        # במקרה של כשל - איפוס כל החיבורים והדפסת שגיאה
        self.client = None
        self.db = None  
        self.collection = None

# שורות 46-50: הקמת אינדקס ייחודי למניעת כפילות ID
async def _setup_indexes(self):
    if self.collection is not None:
        # יצירת אינדקס ייחודי על שדה ה-'ID' - מונע הכנסה של ID זהה פעמיים
        await self.collection.create_index("ID", unique=True)

# שורות 57-66: קריאת כל החיילים מהמסד
async def get_all_data(self) -> List[Dict[str, Any]]:
    # שורות 59-60: ★ בדיקה קריטית ★ 
    # אם החיבור נכשל, self.collection יהיה None
    if self.collection is None:
        raise RuntimeError("Database connection is not available.")
    
    items: List[Dict[str, Any]] = []
    # שורה 63: 'async for' - לולאה א-סינכרונית שמושכת מסמכים אחד אחד
    async for item in self.collection.find({}):  # {} = כל המסמכים
        # שורה 64: המרת ObjectId למחרוזת (JSON לא יודע מה זה ObjectId)
        item["_id"] = str(item["_id"])
        items.append(item)
    return items

# שורות 78-90: יצירת חייל חדש
async def create_item(self, item: SoldierCreate) -> Dict[str, Any]:
    if self.collection is None:
        raise RuntimeError("Database connection is not available.")
    try:
        # שורה 83: המרת המודל Pydantic למילון
        item_dict = item.model_dump()
        # שורה 84: הכנסת המסמך למסד הנתונים
        insert_result = await self.collection.insert_one(item_dict)
        # שורות 85-90: אחזור המסמך שנוצר (כולל ה-_id שנוסף אוטומטית)
        created_item = await self.collection.find_one({"_id": insert_result.inserted_id})
        if created_item:
            created_item["_id"] = str(created_item["_id"])
        return created_item
    except DuplicateKeyError:
        # שורה 92: אם ID כבר קיים, זריקת שגיאה ברורה
        raise ValueError(f"Item with ID {item.ID} already exists.")

# שורות 94-113: עדכון חייל קיים
async def update_item(self, item_id: int, item_update: SoldierUpdate) -> Optional[Dict[str, Any]]:
    if self.collection is None:
        raise RuntimeError("Database connection is not available.")
    
    # שורה 101: יצירת מילון רק עם השדות שהשתנו (exclude_unset=True)
    update_data = item_update.model_dump(exclude_unset=True)
    
    # שורות 103-104: אם אין מה לעדכן, החזרת החייל כמו שהוא
    if not update_data:
        return await self.get_item_by_id(item_id)
    
    # שורות 106-113: עדכון המסמך ב-MongoDB והחזרתו מעודכן
    result = await self.collection.find_one_and_update(
        {"ID": item_id},           # מציאת המסמך לפי ID
        {"$set": update_data},     # עדכון השדות החדשים
        return_document=True       # החזרת המסמך המעודכן
    )
    if result:
        result["_id"] = str(result["_id"])
    return result
```

---

## 4. `crud/soldiers.py` - שכבת ה-API (הראוטר)

קובץ זה מגדיר את נקודות הקצה של ה-API ומכיל את לוגיקת ה-HTTP. הוא "מתרגם" בין העולם של HTTP לעולם של מסד הנתונים.

```python
# שורות 4, 8: ייבוא הכלים מ-FastAPI והמודלים שלנו
from fastapi import APIRouter, HTTPException, status
from ..dependencies import data_loader  # המופע המשותף של DataLoader

# שורות 11-16: ★ יצירת APIRouter ★
router = APIRouter(
    prefix="/soldiersdb",        # כל הכתובות כאן יתחילו ב-/soldiersdb
    tags=["Soldiers CRUD"],      # קיבוץ בתיעוד Swagger
)

# שורות 20-37: נקודת קצה ליצירת חייל חדש (POST)
@router.post("/", response_model=models.SoldierInDB, status_code=status.HTTP_201_CREATED)
async def create_soldier(soldier: models.SoldierCreate):
    # 'soldier: models.SoldierCreate' - FastAPI מבצע ולידציה אוטומטית על גוף הבקשה
    try:
        # קריאה לשכבת ה-DAL ליצירת החייל
        created_soldier = await data_loader.create_item(soldier)
        return created_soldier
    except ValueError as e:
        # תפיסת שגיאת 'ID כפול' מה-DAL והפיכתה לשגיאת HTTP 409 Conflict
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except RuntimeError as e:
        # תפיסת שגיאת חיבור מה-DAL והפיכתה ל-503 Service Unavailable
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))

# שורות 41-51: קבלת כל החיילים (GET)
@router.get("/", response_model=List[models.SoldierInDB])
async def read_all_soldiers():
    try:
        return await data_loader.get_all_data()
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))

# שורות 55-71: קבלת חייל בודד לפי ID (GET)
@router.get("/{soldier_id}", response_model=models.SoldierInDB)
async def read_soldier_by_id(soldier_id: int):
    # 'soldier_id: int' - FastAPI מתרגם אוטומטית מה-URL למספר שלם
    try:
        soldier = await data_loader.get_item_by_id(soldier_id)
        if soldier is None:
            # אם החייל לא נמצא, החזרת שגיאה 404
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Soldier with ID {soldier_id} not found"
            )
        return soldier
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))

# שורות 75-91: עדכון חייל קיים (PUT)
@router.put("/{soldier_id}", response_model=models.SoldierInDB)
async def update_soldier(soldier_id: int, soldier_update: models.SoldierUpdate):
    # שני פרמטרים: ID מה-URL ונתוני העדכון מגוף הבקשה
    try:
        updated_soldier = await data_loader.update_item(soldier_id, soldier_update)
        if updated_soldier is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Soldier with ID {soldier_id} not found to update"
            )
        return updated_soldier
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))

# שורות 95-112: מחיקת חייל (DELETE)
@router.delete("/{soldier_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_soldier(soldier_id: int):
    try:
        success = await data_loader.delete_item(soldier_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Soldier with ID {soldier_id} not found to delete"
            )
        # 204 No Content - מחיקה מוצלחת ללא גוף תשובה
        return
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
```

---

## 5. `main.py` - הרכבת האפליקציה

הקובץ הראשי שמחבר את כל החלקים ויוצר את אפליקציית FastAPI המוגמרת.

```python
# שורות 2, 6-7: ייבוא הכלים הדרושים
from contextlib import asynccontextmanager
from fastapi import FastAPI
from .crud import soldiers              # הראוטר שיצרנו
from .dependencies import data_loader   # מופע ה-DataLoader המשותף

# שורות 10-21: ★ ניהול מחזור החיים של האפליקציה ★
@asynccontextmanager
async def lifespan(app: FastAPI):
    # הקוד לפני 'yield' רץ בעליית השרת
    print("Application startup: connecting to database...")
    await data_loader.connect()  # התחברות למסד הנתונים
    yield                        # כאן השרת רץ ומקבל בקשות...
    # הקוד אחרי 'yield' רץ בכיבוי השרת  
    print("Application shutdown: disconnecting from database...")
    data_loader.disconnect()     # התנתקות ממסד הנתונים

# שורות 25-30: יצירת אפליקציית FastAPI הראשית
app = FastAPI(
    lifespan=lifespan,           # העברת פונקציית מחזור החיים
    title="FastAPI MongoDB CRUD Service",
    version="2.0",
    description="A microservice for managing soldier data, deployed on OpenShift."
)

# שורה 34: ★★★ החיבור המרכזי ★★★
# פקודה זו "מחברת" את כל נקודות הקצה שהוגדרו ב-soldiers.py לאפליקציה הראשית
# כל ה-routes מ-soldiers.router הופכים זמינים דרך האפליקציה הראשית
app.include_router(soldiers.router)

# שורות 37-43: נקודת קצה לבדיקת בריאות השרת
@app.get("/")
def health_check_endpoint():
    # משמש את OpenShift לבדיקות readiness ו-liveness
    return {"status": "ok"}
```

---

## זרימת נתונים - דוגמה מלאה

כאשר משתמש שולח בקשה `POST /soldiersdb/` ליצירת חייל חדש:

1. **FastAPI מקבל את הבקשה** ומפנה אותה ל-`soldiers.router`
2. **הראוטר מפעיל** את `create_soldier()` ב-`crud/soldiers.py`
3. **הפונקציה מבצעת ולידציה** על הנתונים באמצעות `SoldierCreate`
4. **קריאה ל-DAL**: `await data_loader.create_item(soldier)`
5. **ה-DAL מתחבר למונגו** ומכניס את המסמך
6. **המסמך חוזר מהמסד** עם `_id` שנוסף אוטומטית  
7. **המרת ObjectId** למחרוזת ב-DAL
8. **החזרת התוצאה** דרך הראוטר ל-FastAPI
9. **FastAPI מבצע סריאליזציה** באמצעות `SoldierInDB` 
10. **החזרת JSON** ללקוח עם קוד סטטוס 201

## עקרונות ארכיטקטוניים

### הפרדת אחריויות (Separation of Concerns)
- **models.py**: רק הגדרות נתונים
- **dal.py**: רק לוגיקת מסד נתונים  
- **crud/soldiers.py**: רק לוגיקת HTTP/API
- **main.py**: רק הרכבה ותצורה
- **dependencies.py**: רק ניהול תלויות

### ניהול שגיאות רב-שכבתי
כל שכבה מטפלת בשגיאות ברמה שלה ומעבירה אותן הלאה בצורה מתאימה.

### קונפיגורציה חיצונית  
כל ההגדרות נקראות ממשתני סביבה, מה שמאפשר פריסה גמישה בסביבות שונות.