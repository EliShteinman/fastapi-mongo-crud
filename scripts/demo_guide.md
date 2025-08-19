# מדריך פריסה ושימוש: אפליקציית FastAPI ו-MongoDB ל-OpenShift

מדריך זה מציג פריסה מלאה של אפליקציה ותשתית ל-OpenShift, שלב אחר שלב.
הוא מכסה שני מסלולי פריסה עיקריים למסד הנתונים:
1. **Deployment:** הדרך הסטנדרטית והגמישה לפריסת רוב היישומים.
2. **StatefulSet:** הדרך המומלצת ליישומים הדורשים זהות רשת יציבה ואחסון קבוע, כמו מסדי נתונים.

בכל מסלול, נדגים שתי שיטות פריסה:
* **דקלרטיבית (עם קבצי YAML):** השיטה המומלצת לפרודקשן (Infrastructure as Code).
* **אימפרטיבית (עם פקודות CLI ישירות):** לשימוש מהיר ולפיתוח.

---

## שלב 0: הכנות מקדימות (משותף לכל המסלולים)

ודא שהכלים הבאים מותקנים ומוכנים לשימוש: `oc`, `docker`, `git`.

### 1. התחברות ל-OpenShift
```bash
oc login --token=<your-token> --server=<your-server-url>
```

### 2. יצירת פרויקט חדש
```bash
oc new-project fastapi-mongo-demo
```

### 3. התחברות ל-Docker Hub
```bash
docker login
```

### 4. הגדרת משתנים
**!!! חשוב:** בצע שלב זה בטרמינל שבו תריץ את שאר הפקודות.

<details>
<summary>💻 <strong>עבור Linux / macOS</strong></summary>

```bash
# !!! החלף את 'your-dockerhub-username' בשם המשתמש שלך !!!
export DOCKERHUB_USERNAME='your-dockerhub-username'
export IMAGE_TAG="demo-$(date +%s)"
export FULL_IMAGE_NAME="docker.io/${DOCKERHUB_USERNAME}/fastapi-mongo-crud:${IMAGE_TAG}"
```

</details>

<details>
<summary>🪟 <strong>עבור Windows (CMD)</strong></summary>

```batch
@REM !!! החלף את 'your-dockerhub-username' בשם המשתמש שלך !!!
set "DOCKERHUB_USERNAME=your-dockerhub-username"
FOR /F "delims=" %%g IN ('powershell -NoProfile -Command "Get-Date -UFormat %s"') DO SET "IMAGE_TAG=demo-%%g"
set "FULL_IMAGE_NAME=docker.io/%DOCKERHUB_USERNAME%/fastapi-mongo-crud:%IMAGE_TAG%"
```
</details>

### 5. בניית והעלאת Docker Image
האימג' ישותף בין כל מסלולי הפריסה.

<details>
<summary>💻 <strong>עבור Linux / macOS</strong></summary>

```bash
echo "Building and pushing image: ${FULL_IMAGE_NAME}"
docker buildx build --platform linux/amd64,linux/arm64 --no-cache -t "${FULL_IMAGE_NAME}" --push .
```

</details>

<details>
<summary>🪟 <strong>עבור Windows (CMD)</strong></summary>

```batch
echo "Building and pushing image: %FULL_IMAGE_NAME%"
docker buildx build --platform linux/amd64,linux/arm64 --no-cache -t "%FULL_IMAGE_NAME%" --push .
```
</details>

---

## מסלול א': פריסה עם `Deployment` (הגישה הסטנדרטית)

### חלק א' - פריסה דקלרטיבית (YAML)
זוהי הדרך המומלצת לפרודקשן.

#### 1. פריסת תשתית MongoDB

**צעד 1.1: יצירת ConfigMap למידע תצורה**

הקובץ `00-mongo-configmap.yaml` מכיל הגדרות תצורה לא-רגישות של MongoDB:
```bash
oc apply -f infrastructure/k8s/00-mongo-configmap.yaml
```
*מה זה עושה:* יוצר ConfigMap ששומר שם משתמש root, שם מסד נתונים ושם אוסף.

**צעד 1.2: יצירת Secret לסיסמה**

הקובץ `01-mongo-secret.yaml` מכיל מידע רגיש מוצפן:
```bash
oc apply -f infrastructure/k8s/01-mongo-secret.yaml
```
*מה זה עושה:* יוצר Secret עם סיסמת root מוצפנת של MongoDB.

**צעד 1.3: יצירת PVC לאחסון קבוע**

הקובץ `02-mongo-pvc.yaml` מבקש אחסון קבוע:
```bash
oc apply -f infrastructure/k8s/02-mongo-pvc.yaml
```
*מה זה עושה:* יוצר בקשה לקבלת 2GB אחסון קבוע כדי שהמידע של MongoDB לא יאבד בעת הפעלה מחדש.

**צעד 1.4: יצירת Deployment של MongoDB**

הקובץ `03-mongo-deployment.yaml` מגדיר איך להריץ את MongoDB:
```bash
oc apply -f infrastructure/k8s/03-mongo-deployment.yaml
```
*מה זה עושה:* יוצר Deployment שמריץ pod של MongoDB עם כל ההגדרות, probes לבדיקת בריאות, וחיבור לאחסון הקבוע.

**צעד 1.5: יצירת Service למסד הנתונים**

הקובץ `04-mongo-service.yaml` חושף את MongoDB לתוך הקלאסטר:
```bash
oc apply -f infrastructure/k8s/04-mongo-service.yaml
```
*מה זה עושה:* יוצר Service בשם `mongo-db-service` שמאפשר לאפליקציות אחרות להתחבר למסד הנתונים.

**צעד 1.6: המתנה לאתחול MongoDB**
```bash
echo "Waiting for MongoDB pod to become ready..."
oc wait --for=condition=ready pod -l app.kubernetes.io/instance=mongo-db --timeout=300s
echo "MongoDB pod is ready. Allowing time for internal initialization..."
sleep 15
echo "MongoDB is fully initialized!"
```

#### 2. פריסת אפליקציית FastAPI

**צעד 2.1: יצירת Deployment של FastAPI**

הקובץ `05-fastapi-deployment.yaml` מגדיר איך להריץ את האפליקציה שלנו:

<details>
<summary>💻 <strong>עבור Linux / macOS (עם sed)</strong></summary>

```bash
sed -e "s|docker.io/YOUR_DOCKERHUB_USERNAME/fastapi-mongo-crud:latest|${FULL_IMAGE_NAME}|g" \
    "infrastructure/k8s/05-fastapi-deployment.yaml" | oc apply -f -
```
</details>

<details>
<summary>🪟 <strong>עבור Windows (עם PowerShell)</strong></summary>

```batch
powershell -NoProfile -Command "(Get-Content -Raw infrastructure\k8s\05-fastapi-deployment.yaml) -replace 'docker.io/YOUR_DOCKERHUB_USERNAME/fastapi-mongo-crud:latest', '%FULL_IMAGE_NAME%' | oc apply -f -"
```
</details>

*מה זה עושה:* יוצר Deployment עם האימג' שבנינו, מגדיר משתני סביבה לחיבור למסד הנתונים, ומוסיף probes לבדיקת בריאות.

**צעד 2.2: יצירת Service לאפליקציה**

הקובץ `06-fastapi-service.yaml` חושף את האפליקציה בתוך הקלאסטר:
```bash
oc apply -f infrastructure/k8s/06-fastapi-service.yaml
```
*מה זה עושה:* יוצר Service בשם `mongo-api-service` שמאפשר גישה לאפליקציה דרך פורט 8080.

**צעד 2.3: המתנה לאתחול האפליקציה**
```bash
oc wait --for=condition=ready pod -l app.kubernetes.io/instance=mongo-api --timeout=300s
echo "FastAPI is ready!"
```

#### 3. חשיפת האפליקציה לאינטרנט

**צעד 3.1: יצירת Route**

הקובץ `07-fastapi-route.yaml` חושף את האפליקציה לאינטרנט:
```bash
oc apply -f infrastructure/k8s/07-fastapi-route.yaml
echo "Route created."
```
*מה זה עושה:* יוצר Route ב-OpenShift שנותן לנו URL ציבורי להגיע לאפליקציה עם HTTPS.

**כעת, דלג לשלב "שימוש ובדיקת ה-API".**

---

### חלק ב' - פריסה אימפרטיבית (פקודות ישירות)
שיטה זו משתמשת בפקודות CLI ישירות במקום קבצי YAML.
(ודא שאין משאבים קיימים מהחלק הקודם).

#### 1. פריסת תשתית MongoDB

**צעד 1.1: יצירת ConfigMap**
```bash
oc create configmap mongo-db-config \
  --from-literal=MONGO_INITDB_ROOT_USERNAME=mongoadmin \
  --from-literal=MONGO_DB_NAME=enemy_soldiers \
  --from-literal=MONGO_COLLECTION_NAME=soldier_details
```
*מה זה עושה:* יוצר ConfigMap עם הגדרות תצורה של MongoDB.

**צעד 1.2: יצירת Secret**
```bash
oc create secret generic mongo-db-credentials \
  --from-literal=MONGO_INITDB_ROOT_PASSWORD='yourSuperSecretPassword123'
```
*מה זה עושה:* יוצר Secret עם סיסמת root של MongoDB.

**צעד 1.3: יצירת PVC (משתמשים בקובץ YAML)**
```bash
oc apply -f infrastructure/k8s/02-mongo-pvc.yaml
```
*מה זה עושה:* אין דרך פשוטה ליצור PVC באופן אימפרטיבי, לכן משתמשים בקובץ.

**צעד 1.4: יצירת Deployment של MongoDB**
```bash
# יוצר את ה-Deployment הבסיסי
oc create deployment mongo-db-deployment --image=mongo:8.0

# מוסיף פורט לקונטיינר (נחוץ כדי לחשוף אותו אחר כך)
oc patch deployment mongo-db-deployment -p '{"spec":{"template":{"spec":{"containers":[{"name":"mongo","ports":[{"containerPort":27017}]}]}}}}'

# מחבר את האחסון הקבוע
oc set volume deployment/mongo-db-deployment \
  --add --name=mongo-persistent-storage \
  --type=pvc --claim-name=mongo-db-pvc \
  --mount-path=/data/db

# מוסיף משתני סביבה מה-ConfigMap וה-Secret
oc set env deployment/mongo-db-deployment --from=configmap/mongo-db-config
oc set env deployment/mongo-db-deployment --from=secret/mongo-db-credentials

# מוסיף labels לניהול
oc label deployment mongo-db-deployment \
  app.kubernetes.io/instance=mongo-db \
  app.kubernetes.io/name=mongo \
  app.kubernetes.io/part-of=mongo-loader-app
```

**צעד 1.5: יצירת Service**
```bash
# חושף את ה-Deployment כ-Service
oc expose deployment mongo-db-deployment --port=27017 --name=mongo-db-service

# מוסיף labels ל-Service
oc label service mongo-db-service \
  app.kubernetes.io/instance=mongo-db \
  app.kubernetes.io/name=mongo \
  app.kubernetes.io/part-of=mongo-loader-app
```

**צעד 1.6: המתנה לאתחול**
```bash
echo "Waiting for MongoDB pod to become ready..."
oc wait --for=condition=ready pod -l app.kubernetes.io/instance=mongo-db --timeout=300s
echo "MongoDB pod is ready. Allowing time for internal initialization..."
sleep 15
echo "MongoDB is fully initialized!"
```

#### 2. פריסת אפליקציית FastAPI

**צעד 2.1: יצירת Deployment של FastAPI**

<details>
<summary>💻 <strong>עבור Linux / macOS</strong></summary>

```bash
# יוצר את ה-Deployment עם האימג' שלנו
oc create deployment mongo-api-deployment --image="${FULL_IMAGE_NAME}"

# מוסיף משתני סביבה
oc set env deployment/mongo-api-deployment \
  MONGO_HOST=mongo-db-service \
  MONGO_PORT=27017
oc set env deployment/mongo-api-deployment --from=configmap/mongo-db-config
oc set env deployment/mongo-api-deployment --from=secret/mongo-db-credentials

# מוסיף labels
oc label deployment mongo-api-deployment \
  app.kubernetes.io/instance=mongo-api \
  app.kubernetes.io/name=fastapi-mongo \
  app.kubernetes.io/part-of=mongo-loader-app
```

</details>

<details>
<summary>🪟 <strong>עבור Windows (CMD)</strong></summary>

```batch
@REM יוצר את ה-Deployment עם האימג' שלנו
oc create deployment mongo-api-deployment --image="%FULL_IMAGE_NAME%"

@REM מוסיף משתני סביבה
oc set env deployment/mongo-api-deployment MONGO_HOST=mongo-db-service MONGO_PORT=27017
oc set env deployment/mongo-api-deployment --from=configmap/mongo-db-config
oc set env deployment/mongo-api-deployment --from=secret/mongo-db-credentials

@REM מוסיף labels
oc label deployment mongo-api-deployment app.kubernetes.io/instance=mongo-api app.kubernetes.io/name=fastapi-mongo app.kubernetes.io/part-of=mongo-loader-app
```
</details>

**צעד 2.2: יצירת Service לאפליקציה**
```bash
# חושף את האפליקציה כ-Service
oc expose deployment mongo-api-deployment --port=8080 --name=mongo-api-service

# מוסיף labels ל-Service
oc label service mongo-api-service \
  app.kubernetes.io/instance=mongo-api \
  app.kubernetes.io/name=fastapi-mongo \
  app.kubernetes.io/part-of=mongo-loader-app
```

**צעד 2.3: המתנה לאתחול**
```bash
echo "Waiting for FastAPI pod to become ready..."
oc wait --for=condition=ready pod -l app.kubernetes.io/instance=mongo-api --timeout=300s
echo "FastAPI is ready!"
```

#### 3. חשיפת האפליקציה לאינטרנט
```bash
# יוצר Route לגישה חיצונית
oc expose service mongo-api-service --name=mongo-api-route

# מוסיף labels ל-Route
oc label route mongo-api-route \
  app.kubernetes.io/instance=mongo-api \
  app.kubernetes.io/name=fastapi-mongo \
  app.kubernetes.io/part-of=mongo-loader-app

echo "Route created."
```
**כעת, דלג לשלב "שימוש ובדיקת ה-API".**

---

## מסלול ב': פריסה עם `StatefulSet` (הגישה המתקדמת)

### 1. פריסת תשתית MongoDB

**צעד 1.1: יצירת ConfigMap ו-Secret**
```bash
oc apply -f infrastructure/k8s/00-mongo-configmap.yaml
oc apply -f infrastructure/k8s/01-mongo-secret.yaml
```
*מה זה עושה:* זהה למסלול הקודם - יוצר תצורה וסיסמה.

**צעד 1.2: יצירת StatefulSet**

הקובץ `03a-mongo-statefulset.yaml` יוצר StatefulSet במקום Deployment:
```bash
oc apply -f infrastructure/k8s/03a-mongo-statefulset.yaml
```
*מה זה עושה:* יוצר StatefulSet שמנהל את האחסון הקבוע באופן אוטומטי ונותן זהות יציבה לכל Pod.

**צעד 1.3: יצירת Headless Service**

הקובץ `04a-mongo-headless-service.yaml` יוצר Service מיוחד ל-StatefulSet:
```bash
oc apply -f infrastructure/k8s/04a-mongo-headless-service.yaml
```
*מה זה עושה:* יוצר Headless Service (בלי ClusterIP) שנותן לכל Pod ב-StatefulSet כתובת רשת ייחודית ויציבה.

**צעד 1.4: המתנה לאתחול**
```bash
echo "Waiting for MongoDB StatefulSet pod to become ready..."
oc wait --for=condition=ready pod -l app.kubernetes.io/instance=mongo-db --timeout=300s
echo "MongoDB pod is ready. Allowing time for internal initialization..."
sleep 15
echo "MongoDB is fully initialized!"
```

### 2. פריסת אפליקציית FastAPI

**צעד 2.1: יצירת Deployment של FastAPI (מותאם ל-StatefulSet)**

הקובץ `05a-fastapi-deployment-for-statefulset.yaml` מותאם להתחבר ל-Headless Service:

<details>
<summary>💻 <strong>עבור Linux / macOS (עם sed)</strong></summary>

```bash
sed -e "s|docker.io/YOUR_DOCKERHUB_USERNAME/fastapi-mongo-crud:latest|${FULL_IMAGE_NAME}|g" \
    "infrastructure/k8s/05a-fastapi-deployment-for-statefulset.yaml" | oc apply -f -
```
</details>

<details>
<summary>🪟 <strong>עבור Windows (עם PowerShell)</strong></summary>

```batch
powershell -NoProfile -Command "(Get-Content -Raw infrastructure\k8s\05a-fastapi-deployment-for-statefulset.yaml) -replace 'docker.io/YOUR_DOCKERHUB_USERNAME/fastapi-mongo-crud:latest', '%FULL_IMAGE_NAME%' | oc apply -f -"
```
</details>

*מה זה עושה:* יוצר Deployment של האפליקציה שמתחבר ל-`mongo-db-headless-service` במקום ל-Service רגיל.

**צעד 2.2: יצירת Service לאפליקציה**

הקובץ `06a-fastapi-service-for-statefulset.yaml` יוצר Service עם שמות מותאמים:
```bash
oc apply -f infrastructure/k8s/06a-fastapi-service-for-statefulset.yaml
```

**צעד 2.3: המתנה לאתחול**
```bash
oc wait --for=condition=ready pod -l app.kubernetes.io/instance=mongo-api-stateful --timeout=300s
echo "FastAPI is ready!"
```

### 3. חשיפת האפליקציה

**צעד 3.1: יצירת Route מותאם ל-StatefulSet**

הקובץ `07a-fastapi-route-for-statefulset.yaml` יוצר Route עם שם מותאם:
```bash
oc apply -f infrastructure/k8s/07a-fastapi-route-for-statefulset.yaml
echo "Route created."
```

---

## שלב 3: שימוש ובדיקת ה-API

לאחר שהפריסה הושלמה, מצא את כתובת ה-URL של האפליקציה.

<details>
<summary>💻 <strong>עבור Linux / macOS</strong></summary>

```bash
# בחר את השורה המתאימה למסלול הפריסה שלך:

# עבור מסלול Deployment (רגיל או אימפרטיבי):
export ROUTE_URL=$(oc get route mongo-api-route -o jsonpath='{.spec.host}')

# עבור מסלול StatefulSet:
# export ROUTE_URL=$(oc get route mongo-api-route-stateful -o jsonpath='{.spec.host}')

echo "Application URL: https://${ROUTE_URL}"
echo "API Documentation: https://${ROUTE_URL}/docs"
```
</details>

<details>
<summary>🪟 <strong>עבור Windows (CMD)</strong></summary>

```batch
@REM בחר את השורה המתאימה למסלול הפריסה שלך:

@REM עבור מסלול Deployment (רגיל או אימפרטיבי):
FOR /F "usebackq delims=" %%g IN (`oc get route mongo-api-route -o jsonpath={.spec.host}`) DO SET "ROUTE_URL=%%g"

@REM עבור מסלול StatefulSet:
@REM FOR /F "usebackq delims=" %%g IN (`oc get route mongo-api-route-stateful -o jsonpath={.spec.host}`) DO SET "ROUTE_URL=%%g"

echo Application URL: https://%ROUTE_URL%
echo API Documentation: https://%ROUTE_URL%/docs
```
</details>

### דוגמאות שימוש עם `curl`

<details>
<summary>💻 <strong>עבור Linux / macOS</strong></summary>

**1. קבלת כל החיילים**
```bash
curl "https://${ROUTE_URL}/soldiersdb/" | jq
```

**2. יצירת חייל חדש**
```bash
curl -X POST "https://${ROUTE_URL}/soldiersdb/" \
  -H "Content-Type: application/json" \
  -d '{"ID": 101, "first_name": "John", "last_name": "Doe", "phone_number": 5551234, "rank": "Sergeant"}'
```

**3. קבלת חייל ספציפי (ID=101)**
```bash
curl "https://${ROUTE_URL}/soldiersdb/101" | jq
```

**4. עדכון חייל (ID=101)**
```bash
curl -X PUT "https://${ROUTE_URL}/soldiersdb/101" \
  -H "Content-Type: application/json" \
  -d '{"rank": "Captain", "phone_number": 5555678}'
```

**5. מחיקת חייל (ID=101)**
```bash
curl -X DELETE "https://${ROUTE_URL}/soldiersdb/101"
```

</details>

<details>
<summary>🪟 <strong>עבור Windows (CMD)</strong></summary>

**1. קבלת כל החיילים**
```batch
curl "https://%ROUTE_URL%/soldiersdb/" | jq
```

**2. יצירת חייל חדש**
```batch
curl -X POST "https://%ROUTE_URL%/soldiersdb/" ^
  -H "Content-Type: application/json" ^
  -d "{\"ID\": 101, \"first_name\": \"John\", \"last_name\": \"Doe\", \"phone_number\": 5551234, \"rank\": \"Sergeant\"}"
```

**3. קבלת חייל ספציפי (ID=101)**
```batch
curl "https://%ROUTE_URL%/soldiersdb/101" | jq
```

**4. עדכון חייל (ID=101)**
```batch
curl -X PUT "https://%ROUTE_URL%/soldiersdb/101" ^
  -H "Content-Type: application/json" ^
  -d "{\"rank\": \"Captain\", \"phone_number\": 5555678}"
```

**5. מחיקת חייל (ID=101)**
```batch
curl -X DELETE "https://%ROUTE_URL%/soldiersdb/101"
```

</details>

---

## שלב 4: ניקוי הסביבה

### אפשרות א': מחיקה סלקטיבית באמצעות תוויות
```bash
# מחיקת כל הרכיבים ששייכים לאפליקציה
oc delete all,pvc,secret,configmap -l app.kubernetes.io/part-of=mongo-loader-app
```

### אפשרות ב': מחיקת הפרויקט כולו
```bash
oc delete project fastapi-mongo-demo
```

---

## טיפים ופתרון בעיות

### בדיקת סטטוס הרכיבים
```bash
# בדיקת כל ה-pods
oc get pods

# בדיקת logs של MongoDB
oc logs -l app.kubernetes.io/instance=mongo-db

# בדיקת logs של FastAPI
oc logs -l app.kubernetes.io/instance=mongo-api

# בדיקת Routes
oc get routes
```

### בעיות נפוצות
1. **Pod לא עולה:** בדוק logs עם `oc logs <pod-name>`
2. **לא ניתן להגיע לאפליקציה:** ודא שה-Route נוצר בהצלחה
3. **בעיות חיבור למסד נתונים:** ודא שה-Service של MongoDB פועל
4. **בעיות אחסון:** בדוק שה-PVC נוצר ומקושר