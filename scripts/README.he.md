# תיקיית Scripts - סקריפטי פריסה ובדיקה

🌍 **שפה:** [English](README.md) | **[עברית](README.he.md)**

תיקייה זו מכילה את כל הכלים הדרושים לפריסה ובדיקה אוטומטית של אפליקציית FastAPI MongoDB. כל סקריפט מתוכנן לפעול באופן עצמאי ומספק אוטומציה מלאה.

## קבצים בתיקייה

### 🚀 סקריפטי פריסה אוטומטית
- **`deploy.sh` / `deploy.bat`** - פריסה סטנדרטית (Deployment + PVC)
- **`deploy-statefulset.sh` / `deploy-statefulset.bat`** - פריסה מתקדמת (StatefulSet)
- **`run_api_tests.sh`** - בדיקות API מקצה לקצה

### 📚 מדריכים
- **`demo_guide.he.md`** - 📖 **מדריך פריסה ידנית עצמאי** - מלמד פריסה שלב אחר שלב ללא סקריפטים

---

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

---

## ניתוח מפורט של הסקריפטים

### 🤖 סקריפטי הפריסה האוטומטית

#### סקריפט 1: `deploy.sh/bat` - הגישה הסטנדרטית

**מה הסקריפט עושה:**

1. **בדיקות מקדימות:**
   ```bash
   # וידוא שרץ מספריית הפרויקט
   PROJECT_ROOT=$(git rev-parse --show-toplevel)
   cd "$PROJECT_ROOT"
   
   # בדיקת פרמטרים
   if [ -z "$1" ]; then
       echo "ERROR: Docker Hub username required"
       exit 1
   fi
   ```

2. **יצירת תג ייחודי לאימג':**
   ```bash
   # משתמש ב-git commit או timestamp
   IMAGE_TAG=$(git rev-parse --short HEAD 2>/dev/null || date +%s)
   FULL_IMAGE_NAME="docker.io/${DOCKERHUB_USERNAME}/fastapi-mongo-crud:${IMAGE_TAG}"
   ```
   
   **למה תג ייחודי?** מבטיח שכל פריסה משתמשת באימג' חדש, מונע cache issues.

3. **בניה והעלאה מתקדמת:**
   ```bash
   docker buildx build --platform linux/amd64,linux/arm64 --no-cache -t "${FULL_IMAGE_NAME}" --push .
   ```
   
   **למה `buildx`?** תמיכה ב-multi-platform (Intel ו-ARM), חשוב לפריסה בענן.

4. **פריסת MongoDB (Deployment):**
   ```bash
   oc apply -f infrastructure/k8s/00-mongo-configmap.yaml
   oc apply -f infrastructure/k8s/01-mongo-secret.yaml
   oc apply -f infrastructure/k8s/02-mongo-pvc.yaml        # ★ PVC נפרד ★
   oc apply -f infrastructure/k8s/03-mongo-deployment.yaml
   oc apply -f infrastructure/k8s/04-mongo-service.yaml
   ```

5. **המתנה חכמה ל-MongoDB:**
   ```bash
   oc wait --for=condition=ready pod -l app.kubernetes.io/instance=mongo-db --timeout=300s
   sleep 15  # זמן נוסף לאתחול פנימי
   ```
   
   **למה שני שלבים?** `wait` מחכה ש-pod יעלה, `sleep` נותן זמן ל-MongoDB להיות מוכן לחיבורים.

6. **פריסת FastAPI עם החלפת אימג':**
   ```bash
   sed -e "s|docker.io/YOUR_DOCKERHUB_USERNAME/fastapi-mongo-crud:latest|${FULL_IMAGE_NAME}|g" \
       "infrastructure/k8s/05-fastapi-deployment.yaml" | oc apply -f -
   ```
   
   **טריק ה-sed:** מחליף placeholder באימג' האמיתי בזמן אמת.

#### סקריפט 2: `deploy-statefulset.sh/bat` - הגישה המתקדמת

**ההבדלים העיקריים:**

1. **ללא PVC נפרד:**
   ```bash
   # אין:
   # oc apply -f 02-mongo-pvc.yaml
   
   # יש:
   oc apply -f infrastructure/k8s/03a-mongo-statefulset.yaml  # ★ אחסון אוטומטי ★
   ```

2. **Headless Service:**
   ```bash
   oc apply -f infrastructure/k8s/04a-mongo-headless-service.yaml
   ```

3. **API מותאם ל-StatefulSet:**
   ```bash
   # מחבר ל-headless service במקום service רגיל
   sed -e "s|docker.io/YOUR_DOCKERHUB_USERNAME/fastapi-mongo-crud:latest|${FULL_IMAGE_NAME}|g" \
       "infrastructure/k8s/05a-fastapi-deployment-for-statefulset.yaml" | oc apply -f -
   ```

**מתי להשתמש בכל סקריפט?**

| תכונה | deploy.sh | deploy-statefulset.sh |
|--------|-----------|---------------------|
| **מהירות פריסה** | מהיר | איטי יותר |
| **אמינות נתונים** | בסיסית | גבוהה |
| **מורכבות** | פשוט | מתוחכם |
| **מתאים ל** | פיתוח/בדיקות | פרודקשן |
| **שחזור נתונים** | ידני | אוטומטי |

### 🧪 סקריפט הבדיקות: `run_api_tests.sh`

זה הסקריפט החכם ביותר - הוא מבצע בדיקת API מקיפה:

#### פאזות הבדיקה:

**פאזה 0: ניקוי מקדים**
```bash
# מוחק נתונים מבדיקות קודמות (אם יש)
curl -s -o /dev/null -X DELETE "${FULL_URL}/${SOLDIER_1_ID}"
curl -s -o /dev/null -X DELETE "${FULL_URL}/${SOLDIER_2_ID}"
```

**פאזה 1: יצירה (CREATE)**
```bash
# בדיקה שהמסד ריק
RESPONSE_BODY=$(curl -s -w "\n%{http_code}" "${FULL_URL}/")
STATUS_CODE=$(echo "$RESPONSE_BODY" | tail -n1)
BODY=$(echo "$RESPONSE_BODY" | sed '$d')

if [ "$STATUS_CODE" = "200" ] && [ "$(echo "$BODY" | jq 'length')" -eq 0 ]; then
    echo "✅ PASSED: Database is empty"
else
    echo "❌ FAILED: Database not empty"
    exit 1
fi
```

**הטריק של curl עם -w:**
- `-w "\n%{http_code}"` מוסיף את status code בסוף
- `tail -n1` לוקח את השורה האחרונה (status code)
- `sed '$d'` מוחק את השורה האחרונה (מחזיר את הbody)

**פאזה 2: בדיקות שגיאות**
```bash
# ניסיון ליצור חייל כפול (צריך להיכשל)
STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${FULL_URL}/" \
  -H "Content-Type: application/json" -d "$JSON_SOLDIER_1")
  
if [ "$STATUS_CODE" = "409" ]; then
    echo "✅ PASSED: Duplicate ID correctly rejected"
else
    echo "❌ FAILED: Expected 409, got $STATUS_CODE"
    exit 1
fi
```

**פאזה 3: CRUD מלא**
- UPDATE עם נתונים חלקיים
- DELETE עם וידוא שהרשומה נמחקה
- בדיקת 404 לרשומות שלא קיימות

**פאזה 4: ניקוי סופי**
```bash
# וידוא שהמסד חזר להיות ריק
RESPONSE_BODY=$(curl -s -w "\n%{http_code}" "${FULL_URL}/")
STATUS_CODE=$(echo "$RESPONSE_BODY" | tail -n1)
BODY=$(echo "$RESPONSE_BODY" | sed '$d')

if [ "$STATUS_CODE" = "200" ] && [ "$(echo "$BODY" | jq 'length')" -eq 0 ]; then
    echo "✅ PASSED: Final cleanup successful"
else
    echo "❌ FAILED: Database not clean after tests"
fi
```

#### מה הסקריפט בודק?

✅ **פונקציונליות:**
- יצירת חיילים חדשים
- קריאת כל החיילים
- קריאת חייל ספציפי
- עדכון חייל קיים
- מחיקת חייל

✅ **טיפול בשגיאות:**
- 409 - חייל כפול
- 404 - חייל לא נמצא
- 422 - נתונים לא תקינים

✅ **עקביות נתונים:**
- נתונים נשמרים אחרי יצירה
- נתונים משתנים אחרי עדכון
- נתונים נמחקים אחרי delete

### 📚 המדריך הידני: `demo_guide.he.md`

זה מדריך **עצמאי לחלוטין** שמלמד איך לפרוס בלי סקריפטים:

#### מה המדריך מכסה:

**חלק 1: הכנות בסיסיות**
- התחברות ל-OpenShift
- בניית Docker image
- הגדרת משתני סביבה

**חלק 2: שני מסלולי פריסה**
- **Deployment:** עם הסבר מפורט של כל קובץ YAML
- **StatefulSet:** עם הדגשת ההבדלים

**חלק 3: שתי שיטות לכל מסלול**
- **דקלרטיבית:** עם קבצי YAML (Infrastructure as Code)
- **אימפרטיבית:** עם פקודות CLI ישירות

**חלק 4: בדיקות מעשיות**
- דוגמאות curl מפורטות
- הסבר על כל endpoint
- טיפול בשגיאות

#### למה המדריך הידני חשוב?

1. **הבנה עמיקה:** מבין מה כל פקודה עושה
2. **פתרון בעיות:** יודע איך לתקן כשמשהו לא עובד
3. **התאמות:** יכול לשנות לפי צרכים ספציפיים
4. **למידה:** מבין את עקרונות Kubernetes/OpenShift

---

## מתי להשתמש בכל כלי?

### השתמש בסקריפטים האוטומטיים אם:
- ✅ אתה רוצה פריסה מהירה
- ✅ זה demo או הצגה
- ✅ אתה סומך על ההגדרות הבסיסיות
- ✅ לא צריך התאמות מיוחדות

### השתמש במדריך הידני אם:
- 📚 אתה רוצה ללמוד ולהבין
- 🔧 צריך התאמות ספציפיות
- 🐛 יש בעיות שצריך לפתור
- 🏗️ בונה סביבת פרודקשן

### השתמש בסקריפט הבדיקות אם:
- 🧪 רוצה לוודא שהכל עובד
- 🔄 עושה CI/CD
- 📊 צריך דוח על תקינות המערכת
- 🚀 לפני העברה לפרודקשן

---

## טיפים מתקדמים לשימוש בסקריפטים

### 1. התאמת הסקריפטים לצרכים שלך

**שינוי גודל אחסון:**
```bash
# ערוך את הקובץ לפני הרצת הסקריפט
sed -i 's/storage: 2Gi/storage: 5Gi/g' infrastructure/k8s/02-mongo-pvc.yaml
```

**שינוי משאבי CPU/Memory:**
```bash
# עבור MongoDB
sed -i 's/memory: "256Mi"/memory: "512Mi"/g' infrastructure/k8s/03-mongo-deployment.yaml
```

### 2. הרצת סקריפטים עם debugging

```bash
# הוסף verbose output
bash -x ./scripts/deploy.sh your-username

# שמור לוגים לקובץ
./scripts/deploy.sh your-username 2>&1 | tee deployment.log
```

### 3. שימוש בסקריפטים ב-CI/CD

```yaml
# דוגמה ל-GitHub Actions
- name: Deploy to OpenShift
  run: |
    # התחבר ל-OpenShift
    oc login --token=${{ secrets.OPENSHIFT_TOKEN }} --server=${{ secrets.OPENSHIFT_SERVER }}
    
    # רוץ את הסקריפט
    ./scripts/deploy-statefulset.sh ${{ secrets.DOCKERHUB_USERNAME }}
    
    # בדוק שהכל עובד
    ./scripts/run_api_tests.sh "https://$(oc get route mongo-api-route-stateful -o jsonpath='{.spec.host}')"
```

### 4. שחזור מכשלונות

```bash
# אם הסקריפט נכשל, נקה ונסה שוב
oc delete all,pvc,secret,configmap -l app.kubernetes.io/part-of=mongo-loader-app

# הרץ שוב
./scripts/deploy.sh your-username
```

### 5. פקודות שימושיות אחרי פריסה

```bash
# בדוק סטטוס של כל הרכיבים
oc get all -l app.kubernetes.io/part-of=mongo-loader-app

# קבל URL של האפליקציה
oc get route -o jsonpath='{.items[0].spec.host}'

# בדוק logs של כל הpods
oc logs -l app.kubernetes.io/part-of=mongo-loader-app --all-containers=true
```

---

## פתרון בעיות נפוצות עם הסקריפטים

### בעיה: "Docker build failed"
**פתרון:**
```bash
# בדוק שDocker רץ
docker version

# התחבר ל-Docker Hub
docker login

# נסה build ידני
docker build -t test-image .
```

### בעיה: "OpenShift project not found"
**פתרון:**
```bash
# בדוק חיבור
oc whoami

# יצור project חדש
oc new-project fastapi-mongo-demo

# הרץ שוב את הסקריפט
```

### בעיה: "Pod stuck in Pending"
**פתרון:**
```bash
# בדוק מה הבעיה
oc describe pod <pod-name>

# בדוק שיש מספיק משאבים
oc describe nodes

# אם זה PVC, בדוק storage class
oc get storageclass
```

### בעיה: "API tests failing"
**פתרון:**
```bash
# בדוק שה-Route קיים
oc get routes

# בדוק שהpods רצים
oc get pods

# בדוק logs של API
oc logs -l app.kubernetes.io/instance=mongo-api
```

הסקריפטים מתוכננים להיות עמידים ולתת הודעות שגיאה ברורות, אבל תמיד אפשר לחזור למדריך הידני אם משהו לא עובד כמו שצריך.