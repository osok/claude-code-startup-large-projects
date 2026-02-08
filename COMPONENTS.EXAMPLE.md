# Project Components

## Summary

| ID | Name | Type | Path | Status |
|----|------|------|------|--------|
| user-ui | User Frontend | frontend | components/user-ui/ | active |
| admin-ui | Admin Frontend | frontend | components/admin-ui/ | pending |
| backend-api | Backend Server | backend | components/backend-api/ | complete |
| base-agent-lib | Base Agent Library | library | components/base-agent-lib/ | complete |
| ext-agent-lib | Extended Agent Library | library | components/ext-agent-lib/ | active |
| data-processor | Data Processor | agent | components/data-processor/ | pending |
| notification-sender | Notification Sender | agent | components/notification-sender/ | pending |

---

## user-ui

| Field | Value |
|-------|-------|
| **Name** | User Frontend |
| **Type** | frontend |
| **Path** | components/user-ui/ |
| **Description** | React application for end users |
| **Language** | TypeScript/React |
| **Depends On** | backend-api |
| **Deployment** | S3/CloudFront |
| **Port** | 3000 |
| **Status** | active |

---

## admin-ui

| Field | Value |
|-------|-------|
| **Name** | Admin Frontend |
| **Type** | frontend |
| **Path** | components/admin-ui/ |
| **Description** | React application for administrators |
| **Language** | TypeScript/React |
| **Depends On** | backend-api |
| **Deployment** | S3/CloudFront |
| **Port** | 3001 |
| **Status** | pending |

---

## backend-api

| Field | Value |
|-------|-------|
| **Name** | Backend Server |
| **Type** | backend |
| **Path** | components/backend-api/ |
| **Description** | REST API serving both frontends |
| **Language** | Go |
| **Depends On** | base-agent-lib |
| **Deployment** | ECS Fargate |
| **Port** | 8080 |
| **Status** | complete |

---

## base-agent-lib

| Field | Value |
|-------|-------|
| **Name** | Base Agent Library |
| **Type** | library |
| **Path** | components/base-agent-lib/ |
| **Description** | Contains BaseAgent abstract class and common utilities |
| **Language** | Python |
| **Status** | complete |

---

## ext-agent-lib

| Field | Value |
|-------|-------|
| **Name** | Extended Agent Library |
| **Type** | library |
| **Path** | components/ext-agent-lib/ |
| **Description** | Abstract agent extending BaseAgent with queue integration |
| **Language** | Python |
| **Depends On** | base-agent-lib |
| **Status** | active |

---

## data-processor

| Field | Value |
|-------|-------|
| **Name** | Data Processor |
| **Type** | agent |
| **Path** | components/data-processor/ |
| **Description** | Processes incoming data feeds and stores results |
| **Language** | Python |
| **Depends On** | ext-agent-lib, backend-api |
| **Deployment** | Docker container |
| **Status** | pending |

---

## notification-sender

| Field | Value |
|-------|-------|
| **Name** | Notification Sender |
| **Type** | agent |
| **Path** | components/notification-sender/ |
| **Description** | Sends notifications via email and push |
| **Language** | Python |
| **Depends On** | ext-agent-lib |
| **Deployment** | Docker container |
| **Status** | pending |
