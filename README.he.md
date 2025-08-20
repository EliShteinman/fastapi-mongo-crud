# שירות FastAPI MongoDB CRUD עבור OpenShift

🌍 **שפה:** [English](README.md) | **[עברית](README.he.md)**

## סקירה כללית

פרויקט זה הוא API RESTful חזק ומוכן לפרודקשן לניהול מסד נתונים של "חיילים", שנבנה עם Python FastAPI ו-MongoDB. מתוכנן לפריסה עננית ב-OpenShift, הוא משמש כתבנית מקיפה לפיתוח ופריסה של מיקרו-שירותים מודרניים, תוך דבקות בשיטות העבודה הטובות ביותר בארכיטקטורת תוכנה ותשתית כקוד.

כל התשתית מוגדרת באמצעות מניפסטים דקלרטיביים של Kubernetes וניתנת לפריסה אוטומטית עם סקריפטים ייעודיים חוצי פלטפורמות.

### תכונות ושיטות עבודה מומלצות המיושמות

-   **API RESTful מלא עם CRUD:** מספק פונקציונליות מלאה של יצירה, קריאה, עדכון ומחיקה (CRUD) עבור מודל הנתונים "חיילים", תוך דבקות בעקרונות REST.
-   **ארכיטקטורת API מודולרית:** משתמש ב-`APIRouter` של FastAPI ובדפוס זריקת תלויות כדי לשמור על לוגיקת API נקייה, מאורגנת וניתנת להרחבה.
-   **DAL א-סינכרוני:** מיישם שכבת גישה לנתונים (DAL) א-סינכרונית בעלת ביצועים גבוהים באמצעות יכולות async של `pymongo`, המנהלת מאגר חיבורים לפעולות מסד נתונים לא חוסמות.
-   **רישום מקיף:** רישום מובנה בכל האפליקציה עם רמות לוג הניתנות להגדרה באמצעות משתני סביבה.
-   **טיפול מתקדם בשגיאות:** טיפול בחריגים רב-שכבתי עם קודי סטטוס HTTP נאותים והודעות שגיאה מפורטות.
-   **ולידציית קלט:** פונקציות עזר למניעת חזרה על קוד ולהבטחת ולידציה עקבית בכל נקודות הקצה.
-   **ניטור בריאות:** נקודות קצה כפולות לבדיקת בריאות - בדיקות liveness בסיסיות ובדיקות readiness מפורטות עם וריפיקציה של קישוריות מסד נתונים.
-   **תשתית דקלרטיבית (IaC):** כל משאבי OpenShift/Kubernetes מוגדרים במניפסטים סטנדרטיים של YAML הממוקמים בספרייה `infrastructure/k8s`.
-   **אסטרטגיות פריסה כפולות:** מספק מניפסטים לפריסת MongoDB באמצעות גם `Deployment` סטנדרטי וגם `StatefulSet` מתקדם (הגישה המומלצת ליישומים stateful).
-   **ניהול תצורה מתקדם:** מיישם הפרדה ברורה בין תצורה לא רגישה (`ConfigMap`) ונתונים רגישים כמו סיסמאות (`Secret`).
-   **אמינות וניטור בריאות:** כולל **probes של liveness ו-readiness** הן עבור ה-API והן עבור מסד הנתונים כדי להבטיח זמינות גבוהה והתאוששות אוטומטית.
-   **ניהול משאבים:** מגדיר `requests` ו-`limits` של CPU וזיכרון כדי להבטיח ביצועים ולמנוע מחסור במשאבים בתוך הקלאסטר.
-   **אוטומציה מלאה:** מספק סקריפטי פריסה חוצי פלטפורמות (`.sh` עבור Linux/macOS ו-`.bat` עבור Windows) להתקנה מלאה בפקודה אחת.
-   **בדיקות מקצה לקצה:** כולל סקריפט בדיקה אוטומטי (`run_api_tests.sh`) לולידציה של פונקציונליות ה-API הפרוס.

---

## מבנה הפרויקט ותיעוד

הפרויקט מאורגן לספריות נפרדות, כל אחת עם תיעוד מפורט משלה.

```
.
├── infrastructure/
│   └── k8s/
│       ├── README.he.md # ➡️ הסבר מעמיק של כל מניפסטי YAML
│       └── ...          # כל מניפסטי Kubernetes/OpenShift
├── services/
│   └── data_loader/
│       ├── crud/
│       │   └── soldiers.py # APIRouter לפעולות CRUD
│       ├── dal.py          # שכבת גישה לנתונים (DAL)
│       ├── dependencies.py # ניהול תצורה ותלויות
│       ├── main.py         # נקודת כניסה ראשית לאפליקציית FastAPI
│       ├── models.py       # מודלי נתונים של Pydantic
│       └── README.he.md    # ➡️ הסבר מעמיק של ארכיטקטורת קוד Python
├── scripts/
│   ├── deploy.sh           # סקריפט פריסה אוטומטית (אסטרטגיית Deployment)
│   ├── deploy.bat          # גרסת Windows
│   ├── deploy-statefulset.sh # סקריפט פריסה אוטומטית (אסטרטגיית StatefulSet)
│   ├── deploy-statefulset.bat# גרסת Windows
│   ├── README.he.md        # ➡️ סקירת סקריפטים והתחלה מהירה
│   ├── demo_guide.md       # ➡️ מדריך פריסה ושימוש ידני שלב אחר שלב
│   └── run_api_tests.sh    # סקריפט בדיקה E2E עבור ה-API
├── example.env             # תבנית משתני סביבה לפיתוח מקומי
├── .gitignore
├── Dockerfile
├── requirements.txt
└── README.he.md            # קובץ זה
```

### ניווט בתיעוד

-   **🚀 התחלה מהירה:** השתמש בסקריפטים האוטומטיים ב-**[scripts/](./scripts/README.he.md)**
-   **📚 מדריך ידני מלא:** עקוב אחר **[מדריך הפריסה והשימוש הידני](scripts/demo_guide.he.md)** להוראות שלב אחר שלב
-   **⚙️ ארכיטקטורת Python:** קרא את **[מדריך ארכיטקטורת Python](./services/data_loader/README.he.md)** כדי להבין את מבנה הקוד
-   **🔧 פרטי תשתית:** קרא את **[מדריך מניפסטי התשתית](./infrastructure/k8s/README.he.md)** כדי להבין את משאבי Kubernetes/OpenShift

---

## פיתוח מקומי

### הגדרת סביבה
1. **העתק תבנית סביבה:**
   ```bash
   cp example.env .env
   ```

2. **לפיתוח מקומי, ערכי ברירת המחדל עובדים כמו שהם** (MongoDB ללא אימות)

3. **אופציונלי: התאם רמת לוג ב-.env:**
   ```bash
   LOG_LEVEL=DEBUG  # עבור לוגים מפורטים
   LOG_LEVEL=INFO   # ברירת מחדל
   LOG_LEVEL=ERROR  # לוגים מינימליים
   ```

### הרצה מקומית
```bash
# התקנת תלויות
pip install -r requirements.txt

# הרצת MongoDB מקומי (באמצעות Docker)
docker run -d -p 27017:27017 --name local-mongo mongo:8.0

# הפעלת האפליקציה
uvicorn services.data_loader.main:app --reload --port 8000
```

### גישה ל-API מקומי
- **אפליקציה:** http://localhost:8000
- **תיעוד API:** http://localhost:8000/docs
- **בדיקת בריאות:** http://localhost:8000/health

---

## פריסה אוטומטית

להתקנה מהירה, השתמש בסקריפטי האוטומציה המסופקים.

### דרישות מוקדמות

1.  גישה לקלאסטר OpenShift וכלי CLI `oc`.
2.  חשבון Docker Hub ואישורים (`docker login`).
3.  Docker daemon פועל (למשל, Docker Desktop).
4.  `git` מותקן לצורך מעקב גרסאות.

### הוראות

ספריית `scripts` מכילה קבצי פריסה אוטומטיים. הרץ את הסקריפט המתאים מ**ספריית שורש** הפרויקט, תוך מתן שם המשתמש שלך ב-Docker Hub כארגומנט ראשון.

#### אסטרטגיה 1: פריסה סטנדרטית
גישה זו משתמשת ב-`Deployment` סטנדרטי של Kubernetes עבור MongoDB.

*   **עבור Linux / macOS:**
    ```bash
    chmod +x ./scripts/deploy.sh
    ./scripts/deploy.sh your-dockerhub-username
    ```

*   **עבור Windows:**
    ```batch
    .\scripts\deploy.bat your-dockerhub-username
    ```

#### אסטרטגיה 2: פריסת StatefulSet
גישה זו משתמשת ב-`StatefulSet` של Kubernetes, שהיא השיטה המומלצת ליישומים stateful כמו מסדי נתונים.

*   **עבור Linux / macOS:**
    ```bash
    chmod +x ./scripts/deploy-statefulset.sh
    ./scripts/deploy-statefulset.sh your-dockerhub-username
    ```

*   **עבור Windows:**
    ```batch
    .\scripts\deploy-statefulset.bat your-dockerhub-username
    ```

הסקריפט יבנה אוטומטית את תמונת Docker, יעלה אותה ל-Docker Hub, יפרוס את כל המשאבים הנחוצים לפרויקט OpenShift שלך, ויציג את ה-URL הסופי של האפליקציה.

---

## בדיקת API

### קבלת URL האפליקציה שלך
ראשית, השג את ה-URL הציבורי של האפליקציה הפרוסה שלך:

**עבור אסטרטגיית Deployment:**
```bash
export API_URL="https://$(oc get route mongo-api-route -o jsonpath='{.spec.host}')"
echo "Application URL: ${API_URL}"
```

**עבור אסטרטגיית StatefulSet:**
```bash
export API_URL="https://$(oc get route mongo-api-route-stateful -o jsonpath='{.spec.host}')"
echo "Application URL: ${API_URL}"
```

### בדיקה אוטומטית
השתמש בסקריפט הבדיקה המסופק לולידציה מקיפה של API:

```bash
# הרצת חבילת הבדיקות האוטומטית
./scripts/run_api_tests.sh "${API_URL}"
```

סקריפט הבדיקה יבצע אוטומטית:
- בדיקת כל פעולות CRUD
- ולידציה של טיפול בשגיאות
- בדיקת התמדה של נתונים
- וריפיקציה של תגובות API
- ניקוי נתוני בדיקה

### דוגמאות בדיקה ידנית
לבדיקות ידניות מהירות:

```bash
# בדוק אם ה-API פועל
curl "${API_URL}/health"

# צפה בתיעוד API
echo "API Documentation: ${API_URL}/docs"
```

---

## פריסה ובדיקת API ידנית

להוראות מפורטות, שלב אחר שלב, על איך לפרוס את האפליקציה ידנית ולבדוק את נקודות הקצה של ה-API באמצעות `curl`, אנא עיין ב-**[מדריך הפריסה והשימוש הידני](scripts/demo_guide.he.md)**.