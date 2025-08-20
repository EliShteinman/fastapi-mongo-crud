# תיעוד מניפסטים של Kubernetes/OpenShift

🌍 **שפה:** [English](README.md) | **[עברית](README.he.md)**

מדריך זה מסביר את התפקיד של כל אחד מקבצי ה-YAML בתיקייה זו, איך הם עובדים יחד, ומה עושה כל חלק חשוב. המדריך מתמקד בהבנה עמיקה של כל רכיב ולמה הוא בנוי כך.

## סקירה כללית

האפליקציה מורכבת משני רכיבים עיקריים:
1. **MongoDB** - מסד הנתונים
2. **FastAPI** - ה-API שמתחבר למסד הנתונים

יש לנו **שני מסלולי פריסה** עם הבדלים משמעותיים:

### מסלול A: Deployment (קבצים רגילים)
- **מתאים לפיתוח ובדיקות**
- PVC נפרד שנוצר מראש
- פשוט יותר להבנה
- MongoDB יכול "לעוף" בין nodes

### מסלול B: StatefulSet (קבצים עם 'a') 
- **מתאים לפרודקשן**
- ניהול אחסון אוטומטי
- זהות רשת יציבה לכל Pod
- סדר פריסה מובטח

---

## רכיבים משותפים (לשני המסלולים)

### `00-mongo-configmap.yaml` - הגדרות לא רגישות

```yaml
data:
  MONGO_INITDB_ROOT_USERNAME: "mongoadmin"    # שם משתמש ראשי
  MONGO_DB_NAME: "enemy_soldiers"             # שם מסד הנתונים (לפי הדרישות!)
  MONGO_COLLECTION_NAME: "soldier_details"   # שם הקולקשן (לפי הדרישות!)
```

**למה ConfigMap ולא Secrets?** 
- ConfigMap לנתונים שאפשר לראות (שמות, הגדרות)
- קל לשנות בלי לבנות מחדש את האימג'
- נגיש לקריאה ועריכה

**למה "enemy_soldiers"?** 
זה שם מסד הנתונים לפי הדרישות הטכניות של הפרויקט.

### `01-mongo-secret.yaml` - סיסמאות מוצפנות

```yaml
data:
  MONGO_INITDB_ROOT_PASSWORD: amhzZHl0dGZlNjVmZHM1NHNjZjY1  # מוצפן base64
```

**למה Secret ולא ConfigMap?**
- סיסמאות חייבות להיות מוצפנות
- OpenShift מצפין אותן אוטומטית במסד הנתונים הפנימי
- לא מופיעות בלוגים או בהדפסות

**איך לפענח את הסיסמה?**
```bash
echo "amhzZHl0dGZlNjVmZHM1NHNjZjY1" | base64 -d
# Output: jhsdyttfe65fds54scf65
```

---

## מסלול A: פריסה עם Deployment (הגישה הסטנדרטית)

### `02-mongo-pvc.yaml` - דרישת אחסון קבוע

```yaml
spec:
  accessModes:
    - ReadWriteOnce    # ★ רק pod אחד יכול לכתוב בו-זמנית ★
  resources:
    requests:
      storage: 2Gi     # דורש 2GB אחסון קבוע
```

**למה PVC נחוץ?**
בלי זה, כל הנתונים של MongoDB יאבדו כשה-pod נהרג או מעודכן. זה כמו להפעיל מסד נתונים על זיכרון RAM - הכל נמחק בכיבוי.

**מה זה ReadWriteOnce?**
- **ReadWriteOnce (RWO)**: רק pod אחד יכול לכתוב
- **ReadWriteMany (RWX)**: מספר pods יכולים לכתוב (לא נתמך בכל הענן)
- **ReadOnlyMany (ROX)**: מספר pods יכולים לקרוא

### `03-mongo-deployment.yaml` - הרצת MongoDB

זה הקובץ הכי מורכב, בואו נפרק אותו:

#### בחירת האימג'
```yaml
image: docker.io/library/mongo:8.0
```
**למה Mongo 8.0?** גרסה יציבה עם תמיכה ארוכת טווח, תואמת ל-AsyncMongoClient של Python.

#### ניהול הגדרות
```yaml
envFrom:
  - configMapRef:
      name: mongo-db-config     # כל המשתנים מה-ConfigMap
  - secretRef:
      name: mongo-db-credentials # כל המשתנים מה-Secret
```

**למה `envFrom` ולא `env`?**
במקום להגדיר כל משתנה בנפרד, אנחנו "שופכים" את כל התוכן של ConfigMap ו-Secret כמשתני סביבה.

#### בדיקות בריאות - ההבדל הקריטי

```yaml
readinessProbe:                # "האם מוכן לקבל תעבורה?"
  exec:
    command: ["mongosh", "--eval", "db.adminCommand('ping')"]
  initialDelaySeconds: 10      # ממתין 10 שניות אחרי שהpod עולה
  periodSeconds: 10           # בודק כל 10 שניות
  timeoutSeconds: 5           # אם לא עונה תוך 5 שניות - נכשל
  failureThreshold: 3         # אחרי 3 כשלונות - מפסיק לשלוח תעבורה (לא הורג!)

livenessProbe:                 # "האם עדיין חי?"
  exec:
    command: ["mongosh", "--eval", "db.adminCommand('ping')"]
  initialDelaySeconds: 30      # ממתין 30 שניות (יותר!) - נותן זמן להתחיל
  periodSeconds: 15           # בודק כל 15 שניות (פחות תדיר)
  timeoutSeconds: 5           # זמן המתנה לתשובה
  failureThreshold: 3         # אחרי 3 כשלונות - הורג את הpod ויוצר חדש!
```

**מה ההבדל?**
- **readinessProbe**: מחליט אם לשלוח תעבורה ל-pod
- **livenessProbe**: מחליט אם להרוג את ה-pod ולהתחיל מחדש

**למה זמנים שונים?**
- readiness מהיר יותר - רוצים לדעת מהר שה-service זמין
- liveness איטי יותר - לא רוצים להרוג pod בגלל עיכוב זמני

#### ניהול משאבים - הלב של הביצועים

```yaml
resources:
  requests:                   # ★ "מינימום מובטח" ★
    cpu: "200m"              # 200 מילי-cores = 0.2 ליבת CPU
    memory: "256Mi"          # 256 מגהבייט RAM
  limits:                     # ★ "מקסימום מותר" ★
    cpu: "500m"              # 0.5 ליבת CPU מקסימום
    memory: "512Mi"          # 512 מגהבייט RAM מקסימום
```

**למה זה קריטי?**
- **requests**: Kubernetes מבטיח שהמשאבים האלה יהיו זמינים
- **limits**: Kubernetes לא נותן לcontainer לחרוג מזה

**מה קורה אם חורגים?**
- **CPU limit**: הcontainer מואט (throttled)
- **Memory limit**: הcontainer נהרג (OOMKilled)

**איך בוחרים ערכים?**
1. התחל עם ניחוש
2. פקח על שימוש באמצעות `kubectl top pods`
3. התאם לפי הצורך

#### חיבור לאחסון הקבוע

```yaml
volumeMounts:
  - name: mongo-persistent-storage
    mountPath: /data/db        # ★ איפה MongoDB שומר את הנתונים ★
volumes:
  - name: mongo-persistent-storage
    persistentVolumeClaim:
      claimName: mongo-db-pvc  # מתחבר ל-PVC שיצרנו
```

**למה `/data/db`?** זוהי הנתיב הסטנדרטי שבו MongoDB שומר את כל הנתונים שלו.

### `04-mongo-service.yaml` - כתובת פנימית למונגו

```yaml
spec:
  selector:
    app.kubernetes.io/instance: mongo-db  # ★ איך Service מוצא את הpods ★
  ports:
    - port: 27017              # פורט סטנדרטי של MongoDB
      targetPort: 27017
```

**מה זה עושה?** 
יוצר כתובת DNS פנימית `mongo-db-service:27017` שה-API יכול להשתמש בה. זה כמו phonebook פנימי של הקלאסטר.

**למה לא IP ישירות?**
כי ה-IP של pods משתנה כל הזמן. ה-Service נותן כתובת יציבה.

### `05-fastapi-deployment.yaml` - הרצת ה-API

#### משתני סביבה מתוחכמים

```yaml
env:
  - name: MONGO_HOST
    value: "mongo-db-service"    # ★ שם ה-Service של MongoDB ★
  - name: MONGO_PORT
    value: "27017"
  - name: MONGO_USER
    valueFrom:
      configMapKeyRef:           # ★ לוקח מה-ConfigMap ★
        name: mongo-db-config
        key: MONGO_INITDB_ROOT_USERNAME
  - name: MONGO_PASSWORD
    valueFrom:
      secretKeyRef:              # ★ לוקח מה-Secret (מוצפן!) ★
        name: mongo-db-credentials
        key: MONGO_INITDB_ROOT_PASSWORD
```

**למה `valueFrom` ולא `value`?**
זה מאפשר לקשר ישירות ל-ConfigMap ו-Secret. אם נשנה את הערך ב-ConfigMap, הpod החדש יקבל את הערך החדש אוטומטית.

#### בדיקות בריאות של ה-API - שני endpoints שונים!

```yaml
readinessProbe:               # "האם מוכן לעבוד?"
  httpGet:
    path: /health             # ★ בודק גם חיבור למסד נתונים! ★
    port: 8080
  initialDelaySeconds: 15     # ממתין 15 שניות אחרי שהpod עולה
  periodSeconds: 10          # בודק כל 10 שניות

livenessProbe:               # "האם עדיין חי?"
  httpGet:
    path: /                  # ★ בודק רק שהשרת עונה ★
    port: 8080
  initialDelaySeconds: 20     # ממתין 20 שניות (יותר מreadiness!)
  periodSeconds: 20          # בודק כל 20 שניות (פחות תדיר)
```

**למה שני endpoints שונים?**
- `/health`: endpoint מתקדם שבודק גם חיבור למסד נתונים
- `/`: endpoint בסיסי שבודק רק שהשרת רץ

זה מונע מצב שבו ה-API "חי" אבל לא יכול להתחבר למסד הנתונים.

#### ניהול משאבים - ה-API צריך פחות

```yaml
resources:
  requests:                  # מינימום מובטח
    cpu: "50m"              # 0.05 ליבת CPU - יישום Python קל
    memory: "128Mi"         # 128 מגהבייט RAM
  limits:                    # מקסימום מותר
    cpu: "200m"             # 0.2 ליבת CPU מקסימום
    memory: "256Mi"         # 256 מגהבייט RAM מקסימום
```

**למה פחות ממונגו?**
API שמטפל בבקשות HTTP בדרך כלל צורך פחות משאבים ממסד נתונים שמחזיק נתונים בזיכרון.

### `06-fastapi-service.yaml` ו-`07-fastapi-route.yaml`

**Service**: יוצר כתובת פנימית `mongo-api-service:8080`

**Route**: יוצר URL ציבורי עם HTTPS אוטומטי:
```yaml
tls:
  termination: edge          # ★ HTTPS אוטומטי ★
  insecureEdgeTerminationPolicy: Redirect  # ★ מפנה HTTP ל-HTTPS ★
```

---

## מסלול B: פריסה עם StatefulSet (הגישה המתקדמת)

### למה StatefulSet טוב יותר למסדי נתונים?

#### 1. זהות יציבה
```bash
# Deployment
mongo-db-deployment-7d4f8b9c8-x7k2m  # שם אקראי
mongo-db-deployment-7d4f8b9c8-p9q1n  # שם אקראי

# StatefulSet  
mongo-db-statefulset-0                # שם קבוע!
mongo-db-statefulset-1                # שם קבוע!
```

#### 2. סדר פריסה מובטח
- Pods עולים בסדר: 0, 1, 2...
- Pod 1 לא יעלה עד שPod 0 מוכן
- חשוב למסדי נתונים עם clustering

#### 3. אחסון אוטומטי לכל Pod
כל Pod מקבל PVC משלו אוטומטית - לא צריך ליצור מראש.

### `03a-mongo-statefulset.yaml` - StatefulSet במקום Deployment

**ההבדלים העיקריים:**

#### שדה serviceName
```yaml
kind: StatefulSet
spec:
  serviceName: "mongo-db-headless-service"  # ★ צריך Headless Service ★
```

#### volumeClaimTemplates - הקסם
```yaml
volumeClaimTemplates:          # ★ יוצר PVC אוטומטית! ★
- metadata:
    name: mongo-persistent-storage
  spec:
    accessModes: [ "ReadWriteOnce" ]
    resources:
      requests:
        storage: 2Gi
```

**מה זה עושה?**
במקום ליצור PVC מראש, StatefulSet יוצר PVC חדש לכל Pod:
- `mongo-persistent-storage-mongo-db-statefulset-0`
- `mongo-persistent-storage-mongo-db-statefulset-1`

### `04a-mongo-headless-service.yaml` - Service מיוחד ל-StatefulSet

```yaml
spec:
  clusterIP: None              # ★ זה מה שעושה אותו "headless" ★
```

**מה זה Headless Service?**
- Service רגיל: יש לו IP אחד שמפנה לכל הpods
- Headless Service: אין לו IP, אבל נותן DNS ייחודי לכל pod

**למה StatefulSet צריך את זה?**
זה נותן לכל Pod כתובת DNS ייחודית:
- `mongo-db-statefulset-0.mongo-db-headless-service`
- `mongo-db-statefulset-1.mongo-db-headless-service`

חשוב למסדי נתונים עם clustering שצריכים לדעת איך להגיע לpod ספציפי.

### קבצי API מותאמים (05a, 06a, 07a)

ההבדל היחיד:
```yaml
# בקבצים רגילים:
MONGO_HOST: "mongo-db-service"

# בקבצים של StatefulSet:
MONGO_HOST: "mongo-db-headless-service"
```

---

## השוואה מפורטת: Deployment vs StatefulSet

| תכונה | Deployment | StatefulSet |
|--------|------------|-------------|
| **שם Pod** | אקראי (hash) | קבוע ומסודר |
| **סדר פריסה** | כל הpods יחד | בסדר, אחד אחרי השני |
| **אחסון** | PVC נפרד, ידני | PVC אוטומטי לכל pod |
| **DNS** | Service רגיל | Headless Service + DNS ייחודי |
| **מתאים ל** | אפליקציות stateless | מסדי נתונים, clustering |
| **מורכבות** | פשוט | מתוחכם יותר |
| **זמן התאוששות** | מהיר | איטי יותר (סדר) |

## דוגמאות לסדר פריסה

### Deployment
```bash
# כל הpods עולים בבת אחת
kubectl apply -f 03-mongo-deployment.yaml

Pod mongo-db-deployment-xxx-abc  Creating...
Pod mongo-db-deployment-xxx-def  Creating...
Pod mongo-db-deployment-xxx-ghi  Creating...
# כולם עולים במקביל
```

### StatefulSet
```bash
# Pods עולים בסדר
kubectl apply -f 03a-mongo-statefulset.yaml

Pod mongo-db-statefulset-0  Creating...
Pod mongo-db-statefulset-0  Ready ✓
Pod mongo-db-statefulset-1  Creating...  # רק אחרי ש-0 מוכן
Pod mongo-db-statefulset-1  Ready ✓
Pod mongo-db-statefulset-2  Creating...  # רק אחרי ש-1 מוכן
```

---

## איך לבחור בין המסלולים?

### השתמש ב-Deployment אם:
- אתה מתחיל ורוצה משהו פשוט
- זה סביבת פיתוח/בדיקות
- לא אכפת לך מאבדן נתונים
- יש לך רק MongoDB אחד
- רוצה פריסה מהירה

### השתמש ב-StatefulSet אם:
- זה סביבת פרודקשן
- חשוב לך שהנתונים ישרדו
- תכנן להגדיל ל-replica set של MongoDB בעתיד
- צריך זהות יציבה לpods
- מוכן להתמודד עם מורכבות נוספת

---

## סדר הפעלה נכון

### Deployment:
```bash
# 1. הגדרות בסיסיות
oc apply -f 00-mongo-configmap.yaml
oc apply -f 01-mongo-secret.yaml

# 2. אחסון ומונגו
oc apply -f 02-mongo-pvc.yaml      # ★ PVC לפני הpod! ★
oc apply -f 03-mongo-deployment.yaml
oc apply -f 04-mongo-service.yaml

# 3. המתן שMongoDB יהיה מוכן
oc wait --for=condition=ready pod -l app.kubernetes.io/instance=mongo-db --timeout=300s

# 4. API
oc apply -f 05-fastapi-deployment.yaml
oc apply -f 06-fastapi-service.yaml
oc apply -f 07-fastapi-route.yaml
```

### StatefulSet:
```bash
# 1. הגדרות בסיסיות
oc apply -f 00-mongo-configmap.yaml
oc apply -f 01-mongo-secret.yaml

# 2. StatefulSet ו-Headless Service
oc apply -f 03a-mongo-statefulset.yaml     # ★ אחסון אוטומטי! ★
oc apply -f 04a-mongo-headless-service.yaml

# 3. המתן שMongoDB יהיה מוכן
oc wait --for=condition=ready pod -l app.kubernetes.io/instance=mongo-db --timeout=300s

# 4. API מותאם
oc apply -f 05a-fastapi-deployment-for-statefulset.yaml
oc apply -f 06a-fastapi-service-for-statefulset.yaml
oc apply -f 07a-fastapi-route-for-statefulset.yaml
```

---

## בדיקת תקינות ופתרון בעיות

### פקודות בדיקה בסיסיות

```bash
# בדוק שכל הpods רצים
oc get pods -l app.kubernetes.io/part-of=mongo-loader-app

# בדוק שהservices זמינים
oc get svc -l app.kubernetes.io/part-of=mongo-loader-app

# קבל את ה-URL הציבורי
oc get route
```

### פתרון בעיות נפוצות

#### Pod לא עולה
```bash
# 1. בדוק סטטוס
oc describe pod <pod-name>

# 2. בדוק logs
oc logs <pod-name>

# 3. בדוק events
oc get events --sort-by=.metadata.creationTimestamp
```

**בעיות נפוצות:**
- `ImagePullBackOff`: בעיה בהורדת image
- `CrashLoopBackOff`: הpod קורס מיד אחרי שעולה
- `Pending`: אין משאבים פנויים או בעיה בPVC

#### אין חיבור למסד נתונים
```bash
# 1. בדוק שמונגו רץ
oc exec -it <mongo-pod> -- mongosh

# 2. בדוק Service
oc describe svc mongo-db-service

# 3. בדוק connectivity
oc exec -it <api-pod> -- nslookup mongo-db-service
```

#### בעיות אחסון
```bash
# בדוק PVC status
oc get pvc

# בדוק אם bound לPV
oc describe pvc mongo-db-pvc

# בדוק storage class
oc get storageclass
```

**Statuses של PVC:**
- `Pending`: מחכה ל-PV זמין
- `Bound`: מחובר בהצלחה ל-PV
- `Lost`: הPV אבד

---

## טיפים מתקדמים

### 1. איך לבדוק שימוש במשאבים
```bash
# שימוש נוכחי
oc top pods

# היסטוריה (אם יש monitoring)
oc describe pod <pod-name> | grep -A 5 "Resource Usage"
```

### 2. איך לשנות גודל אחסון
עבור StatefulSet:
```bash
# ערוך את הtemplate
oc edit statefulset mongo-db-statefulset

# שנה את storage בvolumeClaimTemplates
storage: 5Gi  # במקום 2Gi
```

### 3. איך להעביר מDeployment ל-StatefulSet
```bash
# 1. גבה את הנתונים
oc exec -it <mongo-pod> -- mongodump --archive > backup.archive

# 2. מחק את הDeployment
oc delete -f 03-mongo-deployment.yaml
oc delete -f 02-mongo-pvc.yaml

# 3. פרוס StatefulSet
oc apply -f 03a-mongo-statefulset.yaml

# 4. שחזר נתונים
oc exec -i <new-mongo-pod> -- mongorestore --archive < backup.archive
```

### 4. מוניטורינג ו-alerting
הוסף לpods:
```yaml
metadata:
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "8080"
    prometheus.io/path: "/health"
```

זה יאפשר ל-Prometheus לאסוף metrics מהאפליקציה.