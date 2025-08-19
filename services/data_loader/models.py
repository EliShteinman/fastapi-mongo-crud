from typing import Optional

from pydantic import BaseModel, Field

# זהו "כינוי סוג" (Type Alias) שמבהיר שבקוד שלנו,
# ה-ID של MongoDB (שהוא אובייקט מיוחד) יטופל כמחרוזת טקסט.
PyObjectId = str

# --------------------------------------------------------------------------
# --- מודלים עבור CRUD API ---
# אלו המודלים הגמישים שישמשו אותנו לבניית ה-API המלא.
# --------------------------------------------------------------------------


class SoldierBase(BaseModel):
    """
    מודל בסיסי. מכיל רק את השדות שהמשתמש אמור לספק או לערוך.
    """

    first_name: str
    last_name: str
    phone_number: int
    rank: str


class SoldierCreate(SoldierBase):
    """
    המודל שישמש לקבלת נתונים מהמשתמש ליצירת פריט חדש (בבקשת POST).
    הוא יורש את השדות מ-SoldierBase ומוסיף את ה-ID המספרי.
    """

    ID: int


class SoldierUpdate(BaseModel):
    """
    המודל שישמש לקבלת נתונים לעדכון (בבקשת PUT/PATCH).
    כל השדות אופציונליים, כדי לאפשר עדכון חלקי.
    """

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[int] = None
    rank: Optional[str] = None


class SoldierInDB(SoldierBase):
    """
    מודל המייצג פריט שלם כפי שהוא קיים במסד הנתונים ויוחזר מה-API.
    הוא כולל את כל השדות, כולל אלו שמנוהלים על ידי המערכת.
    """

    # Field(alias='_id') מגשר בין שם השדה ב-MongoDB ('_id')
    # לשם השדה שאנחנו חושפים ב-API ('id').
    id: PyObjectId = Field(alias="_id")
    ID: int  # ה-ID המספרי שלנו

    class Config:
        from_attributes = True
        populate_by_name = True
