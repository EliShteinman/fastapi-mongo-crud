# תיקיית Scripts - סקריפטי פריסה ובדיקה

🌍 **שפה:** [English](README.md) | **[עברית](README.he.md)**

תיקייה זו מכילה את כל הכלים הדרושים לפריסה ובדיקה אוטומטית של אפליקציית FastAPI MongoDB.

## קבצים בתיקייה

### 🚀 סקריפטי פריסה אוטומטית
- **`deploy.sh` / `deploy.bat`** - פריסה סטנדרטית (Deployment + PVC)
- **`deploy-statefulset.sh` / `deploy-statefulset.bat`** - פריסה מתקדמת (StatefulSet)
- **`run_api_tests.sh`** - בדיקות API מקצה לקצה

### 📚 מדריכים
- **`demo_guide.he.md`** - 📖 **מדריך פריסה ידנית עצמאי** - מלמד פריסה שלב אחר שלב ללא סקריפטים

## שתי דרכים לפריסה

### 🚀 **דרך 1: אוטומטית (מהירה)**
השתמש בסקריפטים המוכנים:

```bash
# Linux/macOS - גישה סטנדרטית
./scripts/deploy.sh your-dockerhub-username

# Linux/macOS - גישה מתקדמת (מומלץ)
./scripts/deploy-statefulset.sh your-dockerhub-username

# Windows
.\scripts\deploy.bat your-dockerhub-username
.\scripts\deploy-statefulset.bat your-dockerhub-username
```

### 📚 **דרך 2: ידנית (לימוד מעמיק)**
📖 **למדריך פריסה ידנית מלא עם הסבר כל שלב:**
**[demo_guide.he.md](demo_guide.he.md)**

המדריך מלמד:
- פריסה ידנית של כל הרכיבים
- הבנת המניפסטים
- פקודות `oc` מפורטות  
- דוגמאות `curl` לבדיקת API
- פתרון בעיות

### 🧪 **בדיקת API**
לאחר פריסה (בכל דרך):
```bash
./scripts/run_api_tests.sh https://your-app-url
```

## פרטי הכלים

### 🤖 סקריפטי הפריסה האוטומטית
שני גישות לפריסה מהירה:

1. **גישה סטנדרטית** (`deploy.sh/bat`):
   - משתמש ב-Deployment רגיל + PVC נפרד
   - מתאים לפיתוח ומבחנים

2. **גישה מתקדמת** (`deploy-statefulset.sh/bat`):
   - משתמש ב-StatefulSet + ניהול אחסון אוטומטי
   - מומלץ לפרודקשן

**שני הסקריפטים מבצעים אוטומטית:**
- בניה והעלאה של Docker image
- פריסת MongoDB ו-FastAPI ל-OpenShift  
- יצירת Routes לגישה חיצונית
- הצגת URL סופי

### 🧪 סקריפט הבדיקות
`run_api_tests.sh` מבצע ולידציה מקיפה:
- בדיקת כל פעולות CRUD
- ולידציה של טיפול בשגיאות
- בדיקת persistence של נתונים
- וידוא קודי HTTP תקינים

### 📚 המדריך הידני
`demo_guide.md` הוא מדריך **עצמאי לחלוטין** שמלמד:
- איך לפרוס ידנית בלי סקריפטים
- הבנה מעמיקה של כל רכיב
- שתי שיטות: דקלרטיבית (YAML) ואימפרטיבית (CLI)
- בדיקות API ידניות עם `curl`