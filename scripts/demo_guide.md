# מדריך פריסה ושימוש: אפליקציית FastAPI ו-MongoDB ל-OpenShift

מדריך זה מציג פריסה מלאה של אפליקציה ותשתית ל-OpenShift, שלב אחר שלב.
הוא מכסה שני מסלולי פריסה עיקריים למסד הנתונים:
1.  **Deployment:** הדרך הסטנדרטית והגמישה לפריסת רוב היישומים.
2.  **StatefulSet:** הדרך המומלצת ליישומים הדורשים זהות רשת יציבה ואחסון קבוע וייחודי, כמו מסדי נתונים.

בכל מסלול, נדגים שתי שיטות פריסה:
*   **דקלרטיבית (עם קבצי YAML):** השיטה המומלצת לפרודקשן (Infrastructure as Code).
*   **אימפרטיבית (עם פקודות CLI ישירות):** לשימוש מהיר ולפיתוח.

---

## שלב 0: הכנות מקדימות (משותף לכל המסלולים)

ודא שהכלים הבאים מותקנים ומוכנים לשימוש: `oc`, `docker`, `git`.

#### 1. התחברות ל-OpenShift
```bash
oc login --token=<your-token> --server=<your-server-url>
```

#### 2. יצירת פרויקט חדש
```bash
oc new-project fastapi-mongo-demo
```

#### 3. התחברות ל-Docker Hub
```bash
docker login
```

#### 4. הגדרת משתנים
**!!! חשוב:** בצע שלב זה בטרמינל שבו תריץ את שאר הפקודות.

<details>
<summary>💻 <strong>עבור Linux / macOS</strong></summary>

```bash
# !!! החלף את 'your-dockerhub-username' בשם המשתמש שלך !!!
export DOCKERHUB_USERNAME='your-dockerhub-username'
export IMAGE_TAG=demo-$(date +%s)
```

</details>

<details>
<summary>🪟 <strong>עבור Windows (CMD)</strong></summary>

```batch
@REM !!! החלף את 'your-dockerhub-username' בשם המשתמש שלך !!!
set "DOCKERHUB_USERNAME=your-dockerhub-username"
FOR /F "delims=" %%g IN ('powershell -NoProfile -Command "Get-Date -UFormat %s"') DO SET "IMAGE_TAG=demo-%%g"
```
</details>

#### 5. בניית והעלאת Docker Image
האימג' ישותף בין כל מסלולי הפריסה.

<details>
<summary>💻 <strong>עבור Linux / macOS</strong></summary>

```bash
echo "Building and pushing image: ${DOCKERHUB_USERNAME}/fastapi-mongo-crud:${IMAGE_TAG}"
docker buildx build --platform linux/amd64,linux/arm64 --no-cache -t ${DOCKERHUB_USERNAME}/fastapi-mongo-crud:${IMAGE_TAG} --push .
```

</details>

<details>
<summary>🪟 <strong>עבור Windows (CMD)</strong></summary>

```batch
echo "Building and pushing image: %DOCKERHUB_USERNAME%/fastapi-mongo-crud:%IMAGE_TAG%"
docker buildx build --platform linux/amd64,linux/arm64 --no-cache -t "%DOCKERHUB_USERNAME%/fastapi-mongo-crud:%IMAGE_TAG%" --push .
```
</details>

---
---

## מסלול א': פריסה עם `Deployment` (הגישה הסטנדרטית)
במסלול זה, נשתמש ב-`Deployment` כדי לנהל את ה-Pod של MongoDB.

### חלק א' - פריסה דקלרטיבית (YAML)
זוהי הדרך המומלצת. אנו מריצים את קבצי התצורה שהכנו מראש.

#### 1. פריסת תשתית MongoDB
```bash
# יצירת התצורה, הסודות והאחסון
oc apply -f infrastructure/k8s/00-mongo-configmap.yaml
oc apply -f infrastructure/k8s/01-mongo-secret.yaml
oc apply -f infrastructure/k8s/02-mongo-pvc.yaml

# פריסת ה-Deployment וה-Service
oc apply -f infrastructure/k8s/03-mongo-deployment.yaml
oc apply -f infrastructure/k8s/04-mongo-service.yaml

# המתנה ל-Pod של MongoDB שיהיה מוכן
echo "Waiting for MongoDB pod to become ready..."
oc wait --for=condition=ready pod -l data_loader.kubernetes.io/instance=mongo-db --timeout=300s
sleep 15 # המתנה נוספת לאתחול פנימי של ה-DB
echo "MongoDB is ready!"
```

#### 2. פריסת אפליקציית FastAPI
<details>
<summary>💻 <strong>עבור Linux / macOS (עם sed)</strong></summary>

```bash
sed -e "s|docker.io/YOUR_DOCKERHUB_USERNAME/fastapi-mongo-crud:latest|docker.io/${DOCKERHUB_USERNAME}/fastapi-mongo-crud:${IMAGE_TAG}|g" \
    "infrastructure/k8s/05-fastapi-deployment.yaml" | oc apply -f -
```
</details>
<details>
<summary>🪟 <strong>עבור Windows (עם PowerShell)</strong></summary>

```batch
powershell -NoProfile -Command "(Get-Content -Raw infrastructure\k8s\05-fastapi-deployment.yaml) -replace 'docker.io/YOUR_DOCKERHUB_USERNAME/fastapi-mongo-crud:latest', ('docker.io/{0}/fastapi-mongo-crud:{1}' -f $env:DOCKERHUB_USERNAME, $env:IMAGE_TAG) | oc apply -f -"
```
</details>

```bash
# המשך פריסת ה-API
oc apply -f infrastructure/k8s/06-fastapi-service.yaml
oc wait --for=condition=ready pod -l data_loader.kubernetes.io/instance=mongo-api --timeout=300s
echo "FastAPI is ready!"
```

#### 3. חשיפת האפליקציה
```bash
oc apply -f infrastructure/k8s/07-fastapi-route.yaml
echo "Route created."
```
**כעת, דלג לשלב "שימוש ובדיקת ה-API".**

---

### חלק ב' - פריסה אימפרטיבית (פקודות ישירות)
זוהי דרך מהירה ליצור משאבים, טובה לפיתוח. (ודא שאין משאבים קיימים מהחלק הקודם).

#### 1. פריסת תשתית MongoDB
```bash
# יצירת התצורה והסודות
oc create configmap mongo-db-config --from-literal=MONGO_INITDB_ROOT_USERNAME=mongoadmin --from-literal=MONGO_DB_NAME=mydatabase --from-literal=MONGO_COLLECTION_NAME=data
oc create secret generic mongo-db-credentials --from-literal=MONGO_INITDB_ROOT_PASSWORD='yourSuperSecretPassword123'
oc apply -f infrastructure/k8s/02-mongo-pvc.yaml # אין חלופה אימפרטיבית טובה ל-PVC

# יצירת ה-Deployment
oc create deployment mongo-db-deployment --image=mongo:6.0
oc set volume deployment/mongo-db-deployment --add --name=mongo-persistent-storage --type=pvc --claim-name=mongo-db-pvc --mount-path=/data/db
oc set env deployment/mongo-db-deployment --from=configmap/mongo-db-config
oc set env deployment/mongo-db-deployment --from=secret/mongo-db-credentials
oc label deployment mongo-db-deployment data_loader.kubernetes.io/instance=mongo-db

# יצירת ה-Service
oc expose deployment mongo-db-deployment --port=27017 --name=mongo-db-service
```

#### 2. פריסת אפליקציית FastAPI
```bash
# יצירת ה-Deployment
oc create deployment mongo-api-deployment --image=${DOCKERHUB_USERNAME}/fastapi-mongo-crud:${IMAGE_TAG} # ב-CMD, השתמש ב-%DOCKERHUB_USERNAME% ו-%IMAGE_TAG%
oc set env deployment/mongo-api-deployment --from=configmap/mongo-db-config
oc set env deployment/mongo-api-deployment --from=secret/mongo-db-credentials
oc set env deployment/mongo-api-deployment MONGO_HOST=mongo-db-service MONGO_PORT=27017
oc label deployment mongo-api-deployment data_loader.kubernetes.io/instance=mongo-api

# יצירת ה-Service
oc expose deployment mongo-api-deployment --port=8080 --name=mongo-api-service
```

#### 3. חשיפת האפליקציה
```bash
oc expose service mongo-api-service --name=mongo-api-route
```
**כעת, דלג לשלב "שימוש ובדיקת ה-API".**

---
---

## מסלול ב': פריסה עם `StatefulSet` (הגישה המתקדמת)
במסלול זה, נשתמש ב-`StatefulSet` כדי לנהל את ה-Pod של MongoDB. גישה זו עדיפה למסדי נתונים מכיוון שהיא מספקת זהות רשת יציבה ואחסון קבוע ומובטח.

#### 1. פריסת תשתית MongoDB
```bash
# יצירת התצורה והסודות (זהה)
oc apply -f infrastructure/k8s/00-mongo-configmap.yaml
oc apply -f infrastructure/k8s/01-mongo-secret.yaml

# פריסת ה-StatefulSet וה-Headless Service
# שימו לב: אין צורך ליצור PVC נפרד, ה-StatefulSet יעשה זאת אוטומטית.
oc apply -f infrastructure/k8s/03a-mongo-statefulset.yaml
oc apply -f infrastructure/k8s/04a-mongo-headless-service.yaml

# המתנה ל-Pod של MongoDB שיהיה מוכן
echo "Waiting for MongoDB StatefulSet pod to become ready..."
oc wait --for=condition=ready pod -l data_loader.kubernetes.io/instance=mongo-db --timeout=300s
sleep 15
echo "MongoDB is ready!"
```

#### 2. פריסת אפליקציית FastAPI
נשתמש בקבצים המותאמים ל-StatefulSet.

<details>
<summary>💻 <strong>עבור Linux / macOS (עם sed)</strong></summary>

```bash
sed -e "s|docker.io/YOUR_DOCKERHUB_USERNAME/fastapi-mongo-crud:latest|docker.io/${DOCKERHUB_USERNAME}/fastapi-mongo-crud:${IMAGE_TAG}|g" \
    "infrastructure/k8s/05a-fastapi-deployment-for-statefulset.yaml" | oc apply -f -
```
</details>
<details>
<summary>🪟 <strong>עבור Windows (עם PowerShell)</strong></summary>

```batch
powershell -NoProfile -Command "(Get-Content -Raw infrastructure\k8s\05a-fastapi-deployment-for-statefulset.yaml) -replace 'docker.io/YOUR_DOCKERHUB_USERNAME/fastapi-mongo-crud:latest', ('docker.io/{0}/fastapi-mongo-crud:{1}' -f $env:DOCKERHUB_USERNAME, $env:IMAGE_TAG) | oc apply -f -"
```
</details>

```bash
# המשך פריסת ה-API עם הקבצים החלופיים
oc apply -f infrastructure/k8s/06a-fastapi-service-for-statefulset.yaml
oc wait --for=condition=ready pod -l data_loader.kubernetes.io/instance=mongo-api-stateful --timeout=300s
echo "FastAPI is ready!"
```

#### 3. חשיפת האפליקציה
```bash
oc apply -f infrastructure/k8s/07a-fastapi-route-for-statefulset.yaml
echo "Route created."
```

---
---

## שלב 3: שימוש ובדיקת ה-API

לאחר שהפריסה הושלמה, מצא את כתובת ה-URL של האפליקציה.

<details>
<summary>💻 <strong>עבור Linux / macOS</strong></summary>

```bash
# עבור מסלול Deployment
export ROUTE_URL=$(oc get route mongo-api-route -o jsonpath='{.spec.host}')
# עבור מסלול StatefulSet
# export ROUTE_URL=$(oc get route mongo-api-route-stateful -o jsonpath='{.spec.host}')
echo "Application URL: https://${ROUTE_URL}"
```
</details>
<details>
<summary>🪟 <strong>עבור Windows (CMD)</strong></summary>

```batch
@REM עבור מסלול Deployment
FOR /F "usebackq tokens=*" %%g IN (`oc get route mongo-api-route -o jsonpath={.spec.host}`) DO SET "ROUTE_URL=%%g"

@REM עבור מסלול StatefulSet
@REM FOR /F "usebackq tokens=*" %%g IN (`oc get route mongo-api-route-stateful -o jsonpath={.spec.host}`) DO SET "ROUTE_URL=%%g"

echo Application URL: https://%ROUTE_URL%
```
</details>

#### דוגמאות שימוש עם `curl` (עבור Linux/macOS)

1.  **קבלת כל הפריטים (Endpoint מורשת)**
    ```bash
    curl https://${ROUTE_URL}/data | jq
    ```

2.  **קבלת כל הפריטים (Endpoint חדש)**
    ```bash
    curl https://${ROUTE_URL}/items/ | jq
    ```

3.  **יצירת פריט חדש**
    ```bash
    curl -X POST https://${ROUTE_URL}/items/ \
    -H "Content-Type: application/json" \
    -d '{"ID": 10, "first_name": "New", "last_name": "User"}'
    ```

4.  **קבלת פריט ספציפי (ID=10)**
    ```bash
    curl https://${ROUTE_URL}/items/10
    ```

5.  **עדכון פריט (ID=10)**
    ```bash
    curl -X PUT https://${ROUTE_URL}/items/10 \
    -H "Content-Type: application/json" \
    -d '{"first_name": "Updated"}'
    ```

6.  **מחיקת פריט (ID=10)**
    ```bash
    curl -X DELETE https://${ROUTE_URL}/items/10
    ```

---

## שלב 4: ניקוי הסביבה

### אפשרות א': מחיקה סלקטיבית באמצעות תוויות
```bash
# מחיקת כל הרכיבים ששייכים לאפליקציה
oc delete all,pvc,secret,configmap --selector=data_loader.kubernetes.io/part-of=mongo-loader-data_loader
```

### אפשרות ב': מחיקת הפרויקט כולו
```bash
oc delete project fastapi-mongo-demo
```