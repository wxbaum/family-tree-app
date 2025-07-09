# Family Tree App - Firestore Database Implementation Guide

## 📋 Overview

This document outlines the complete implementation plan for migrating the Family Tree application from PostgreSQL to Google Firestore. This is a clean rewrite approach with no legacy code retention.

**Goal**: Complete Firestore-based family tree application with Firebase authentication
**Timeline**: 2-3 weeks of focused development
**Approach**: Clean rewrite, no migration of existing data

---

## 🎯 Database Schema Design

### Firestore Collections Structure

```
/users/{userId}
  - email: string
  - displayName: string
  - createdAt: timestamp
  - lastActiveAt: timestamp
  - preferences: { theme: string, defaultFamilyTreeId: string }

/family_trees/{familyTreeId}
  - ownerId: string
  - name: string
  - description: string
  - createdAt: timestamp
  - updatedAt: timestamp
  - stats: { peopleCount: number, relationshipCount: number, lastActivity: timestamp }

/family_trees/{familyTreeId}/people/{personId}
  - familyTreeId: string (denormalized)
  - firstName: string
  - lastName: string
  - maidenName: string
  - birthDate: timestamp
  - deathDate: timestamp
  - birthPlace: string
  - deathPlace: string
  - bio: string
  - profilePhotoUrl: string
  - zodiacSign: string
  - chineseZodiac: string
  - numerologyNumber: number
  - createdAt: timestamp
  - updatedAt: timestamp

/family_trees/{familyTreeId}/relationships/{relationshipId}
  - familyTreeId: string (denormalized)
  - fromPersonId: string
  - toPersonId: string
  - relationshipCategory: "family_line" | "partner"
  - generationDifference: -1 | 1 | null
  - relationshipSubtype: string
  - startDate: timestamp
  - endDate: timestamp
  - isActive: boolean
  - notes: string
  - createdAt: timestamp
  - updatedAt: timestamp

/family_trees/{familyTreeId}/files/{fileId}
  - familyTreeId: string (denormalized)
  - personId: string
  - filename: string
  - originalFilename: string
  - filePath: string
  - fileType: "image" | "document" | "video" | "audio" | "other"
  - mimeType: string
  - fileSize: number
  - description: string
  - uploadedAt: timestamp
```

---

## 🚀 Implementation Phases

## Phase 1: Foundation Setup ✅

### Task 1.1: Firebase Configuration ✅ COMPLETED
- [x] Create `backend/app/core/firestore.py` - Firebase client and manager
- [x] Update `backend/app/core/config.py` - Remove SQL, add Firebase settings
- [x] Update `backend/requirements.txt` - Firebase dependencies
- [x] Update `backend/.env` - Firebase configuration
- [x] Create connection test script

### Task 1.2: Base Repository Pattern

**File**: `backend/app/repositories/__init__.py`
```python
# Empty __init__.py file
```

**File**: `backend/app/repositories/base.py`
**Purpose**: Abstract base class for all repositories
**Key Methods**:
- `create(data, doc_id, subcollections)` - Create documents with timestamps
- `get_by_id(doc_id, subcollections)` - Retrieve single document
- `update(doc_id, data, subcollections)` - Update with automatic timestamp
- `delete(doc_id, subcollections)` - Delete document
- `query(filters, order_by, limit, subcollections)` - Query with filters
- `batch_create(items)` - Atomic batch operations
- `get_collection_ref(subcollections)` - Helper for collection references

**Dependencies**: Firestore client, logging, error handling
**Expected Outcome**: Reusable CRUD operations for all entities

---

## Phase 2: Entity Repositories

### Task 2.1: User Repository

**File**: `backend/app/repositories/user_repository.py`
**Purpose**: Manage user documents synced with Firebase Auth
**Key Methods**:
- `create_user(uid, email, display_name)` - Create user from Firebase Auth
- `get_user(uid)` - Get user by Firebase UID
- `update_user(uid, data)` - Update preferences and profile
- `update_last_active(uid)` - Track user activity
- `user_exists(uid)` - Check if user document exists

**Business Logic**:
- Sync with Firebase Auth user creation
- Handle user preferences and app-specific data
- Track last activity for analytics

**Expected Outcome**: Clean user management tied to Firebase Auth

### Task 2.2: Family Tree Repository

**File**: `backend/app/repositories/family_tree_repository.py`
**Purpose**: Manage family tree documents and metadata
**Key Methods**:
- `create_family_tree(owner_id, name, description)` - Create with stats initialization
- `get_family_tree(family_tree_id)` - Get tree with metadata
- `get_user_family_trees(owner_id)` - List user's trees (paginated)
- `update_family_tree(family_tree_id, data)` - Update name/description
- `delete_family_tree(family_tree_id)` - Cascade delete subcollections
- `update_stats(family_tree_id, people_delta, relationships_delta)` - Atomic counters
- `get_tree_statistics(family_tree_id)` - Current stats

**Business Logic**:
- Maintain denormalized stats for performance
- Handle cascade deletion of subcollections
- Atomic updates to prevent race conditions

**Expected Outcome**: Efficient family tree management with accurate statistics

### Task 2.3: Person Repository

**File**: `backend/app/repositories/person_repository.py`
**Purpose**: Manage people within family trees
**Key Methods**:
- `create_person(family_tree_id, person_data)` - Create with familyTreeId denormalization
- `get_person(family_tree_id, person_id)` - Get single person
- `get_people_by_family_tree(family_tree_id, limit, offset)` - List with pagination
- `update_person(family_tree_id, person_id, data)` - Update person data
- `delete_person(family_tree_id, person_id)` - Delete with relationship cleanup
- `search_people(family_tree_id, search_term)` - Search by name
- `get_people_count(family_tree_id)` - Count for statistics
- `batch_create_people(family_tree_id, people_list)` - Bulk operations

**Business Logic**:
- Validate family tree ownership
- Handle astrology field calculations (zodiac signs from birth dates)
- Ensure referential integrity with relationships

**Expected Outcome**: Complete person lifecycle management

### Task 2.4: Relationship Repository

**File**: `backend/app/repositories/relationship_repository.py`
**Purpose**: Manage relationships between people
**Key Methods**:
- `create_relationship(family_tree_id, relationship_data)` - Create with validation
- `get_relationship(family_tree_id, relationship_id)` - Get single relationship
- `get_relationships_by_person(family_tree_id, person_id, category_filter)` - Person's relationships
- `get_family_tree_relationships(family_tree_id)` - All tree relationships
- `update_relationship(family_tree_id, relationship_id, data)` - Update relationship
- `delete_relationship(family_tree_id, relationship_id)` - Delete relationship
- `delete_relationships_by_person(family_tree_id, person_id)` - Cleanup on person deletion
- `validate_relationship(relationship_data)` - Business rule validation
- `get_ancestors(family_tree_id, person_id, generations)` - Traverse family line up
- `get_descendants(family_tree_id, person_id, generations)` - Traverse family line down
- `get_siblings(family_tree_id, person_id)` - Computed from shared parents

**Business Logic**:
- Validate both people exist in same family tree
- Prevent duplicate relationships
- Enforce generation difference rules for family_line
- Handle computed relationships (siblings, extended family)

**Expected Outcome**: Robust relationship management with graph traversal

### Task 2.5: File Repository

**File**: `backend/app/repositories/file_repository.py`
**Purpose**: Manage file metadata (actual files in Google Cloud Storage)
**Key Methods**:
- `create_file_record(family_tree_id, file_data)` - Create metadata record
- `get_file(family_tree_id, file_id)` - Get file metadata
- `get_files_by_person(family_tree_id, person_id, file_type_filter)` - Person's files
- `get_files_by_family_tree(family_tree_id, file_type_filter, limit, offset)` - Tree files
- `update_file_metadata(family_tree_id, file_id, data)` - Update description, etc.
- `delete_file_record(family_tree_id, file_id)` - Delete metadata
- `search_files(family_tree_id, search_term)` - Search by filename/description
- `get_file_statistics(family_tree_id)` - Size and count stats

**Business Logic**:
- Link files to people and family trees
- Track file types and sizes for quotas
- Coordinate with Google Cloud Storage service

**Expected Outcome**: Complete file metadata management

---

## Phase 3: Service Layer Rewrite

### Task 3.1: Family Tree Service Rewrite

**File**: `backend/app/services/family_tree_service.py`
**Purpose**: Business logic for family tree operations
**Dependencies**: FamilyTreeRepository, PersonRepository, RelationshipRepository
**Key Methods**:
- `create_family_tree(owner_id, family_tree_data)` - Create with validation
- `get_family_tree(family_tree_id)` - Get with ownership check
- `get_user_family_trees(owner_id, limit, offset)` - User's trees
- `update_family_tree(family_tree_id, update_data)` - Update with validation
- `delete_family_tree(family_tree_id)` - Cascade delete
- `get_family_tree_graph(family_tree_id)` - Generate React Flow data
- `get_family_tree_statistics(family_tree_id)` - Comprehensive stats

**Business Logic**:
- Ownership validation
- Graph generation for visualization
- Statistics aggregation
- Access control

**Expected Outcome**: Clean service layer for family tree operations

### Task 3.2: Person Service Rewrite

**File**: `backend/app/services/person_service.py`
**Purpose**: Business logic for person operations
**Dependencies**: PersonRepository, RelationshipRepository
**Key Methods**:
- `create_person(person_data)` - Create with astrology calculation
- `get_person(person_id)` - Get with access validation
- `update_person(person_id, update_data)` - Update with validation
- `delete_person(person_id)` - Delete with relationship cleanup
- `search_people(family_tree_id, search_term, limit)` - Search functionality
- `get_person_ancestors(person_id, generations)` - Ancestor traversal
- `get_person_descendants(person_id, generations)` - Descendant traversal
- `get_person_siblings(person_id)` - Computed siblings
- `calculate_person_age(person_id, as_of_date)` - Age calculation
- `calculate_astrology_data(birth_date)` - Zodiac sign calculation

**Business Logic**:
- Astrology feature integration
- Family tree traversal algorithms
- Age and relationship calculations
- Data validation and access control

**Expected Outcome**: Comprehensive person management with relationship features

### Task 3.3: Relationship Service Rewrite

**File**: `backend/app/services/relationship_service.py`
**Purpose**: Business logic for relationship operations
**Dependencies**: RelationshipRepository, PersonRepository
**Key Methods**:
- `create_relationship(relationship_data)` - Create with comprehensive validation
- `get_relationship(relationship_id)` - Get with access validation
- `update_relationship(relationship_id, update_data)` - Update with validation
- `delete_relationship(relationship_id)` - Delete relationship
- `get_person_relationships(person_id, category)` - Person's relationships
- `get_family_tree_relationships(family_tree_id)` - All relationships
- `get_relationship_statistics(family_tree_id)` - Relationship stats
- `find_relationship_path(person1_id, person2_id, max_depth)` - Path finding
- `validate_relationship_data(relationship_data)` - Business rule validation
- `calculate_compatibility(person1_id, person2_id)` - Astrology compatibility

**Business Logic**:
- Relationship validation (no self-relationships, valid people, etc.)
- Graph traversal for path finding
- Astrology compatibility calculations
- Relationship statistics and analytics

**Expected Outcome**: Complete relationship management with astrology features

### Task 3.4: File Service Rewrite

**File**: `backend/app/services/file_service.py`
**Purpose**: File upload/download with Google Cloud Storage
**Dependencies**: FileRepository, Google Cloud Storage client
**Key Methods**:
- `upload_person_file(person_id, file, description)` - Upload to GCS
- `download_person_file(file_id)` - Download from GCS
- `delete_person_file(file_id)` - Delete from GCS and metadata
- `get_person_files(person_id, file_type)` - List person's files
- `get_family_tree_files(family_tree_id, file_type, limit, offset)` - List tree files
- `update_file_metadata(file_id, description)` - Update metadata only
- `validate_file(file)` - File type and size validation
- `get_file_statistics(family_tree_id)` - File usage stats

**Business Logic**:
- Google Cloud Storage integration
- File validation (type, size, content)
- Metadata management
- Access control and cleanup

**Expected Outcome**: Production-ready file management

---

## Phase 4: Authentication Rewrite

### Task 4.1: Firebase Authentication

**File**: `backend/app/core/auth.py`
**Purpose**: Firebase ID token verification and user management
**Key Components**:
- `get_current_user(credentials)` - Verify Firebase ID token
- `CurrentUser` model - User data from Firebase token
- Error handling for invalid tokens
- Integration with user repository for app-specific data

**Business Logic**:
- Firebase ID token verification
- User session management
- Access control for API endpoints

**Expected Outcome**: Secure authentication with Firebase

### Task 4.2: Clean Up Old Models

**Files to Delete**:
- `backend/app/models/database.py` - Delete entire file
- `backend/alembic/` directory - Delete completely
- `backend/app/core/database.py` - Remove SQLAlchemy session management

**Expected Outcome**: Clean codebase with no legacy database code

---

## Phase 5: API Endpoints Rewrite

### Task 5.1: Family Tree Endpoints Rewrite

**File**: `backend/app/api/v1/endpoints/family_trees.py`
**Updates**: 
- Remove SQLAlchemy session dependencies
- Use Firebase auth and Firestore services
- Update all endpoints for new data model

### Task 5.2: People Endpoints Rewrite

**File**: `backend/app/api/v1/endpoints/people.py`
**Updates**:
- Remove SQLAlchemy session dependencies
- Use Firebase auth and Firestore services
- Add astrology endpoints

### Task 5.3: Relationship Endpoints Rewrite

**File**: `backend/app/api/v1/endpoints/relationships.py**
**Updates**:
- Remove SQLAlchemy session dependencies
- Use Firebase auth and Firestore services
- Add relationship path finding endpoints

### Task 5.4: File Endpoints Rewrite

**File**: `backend/app/api/v1/endpoints/files.py`
**Updates**:
- Remove SQLAlchemy session dependencies
- Use Firebase auth and GCS services
- Update for Google Cloud Storage

---

## Phase 6: Application Cleanup

### Task 6.1: Main Application Rewrite

**File**: `backend/app/main.py`
**Updates**:
- Remove database startup/shutdown handlers
- Remove FastAPI Users routes
- Add Firebase initialization
- Clean startup configuration

### Task 6.2: Schema Updates

**File**: `backend/app/schemas/schemas.py`
**Updates**:
- Remove FastAPI Users schema inheritance
- Clean Pydantic models for Firestore
- Remove SQLAlchemy compatibility
- Add astrology field schemas

---

## Phase 7: Testing and Validation

### Task 7.1: Repository Tests

**Create test files for each repository**:
- `backend/tests/test_user_repository.py`
- `backend/tests/test_family_tree_repository.py`
- `backend/tests/test_person_repository.py`
- `backend/tests/test_relationship_repository.py`
- `backend/tests/test_file_repository.py`

**Test Coverage**:
- CRUD operations
- Error handling
- Subcollection operations
- Atomic operations
- Business logic validation

### Task 7.2: Service Tests

**Create test files for each service**:
- `backend/tests/test_family_tree_service.py`
- `backend/tests/test_person_service.py`
- `backend/tests/test_relationship_service.py`
- `backend/tests/test_file_service.py`

**Test Coverage**:
- Integration with repositories
- Business logic validation
- Graph operations
- Astrology calculations

### Task 7.3: API Tests

**Create test files for API endpoints**:
- `backend/tests/test_auth.py`
- `backend/tests/test_family_tree_endpoints.py`
- `backend/tests/test_people_endpoints.py`
- `backend/tests/test_relationship_endpoints.py`
- `backend/tests/test_file_endpoints.py`

**Test Coverage**:
- Firebase auth integration
- Endpoint functionality
- Error handling
- Access control

---

## 📋 Implementation Checklist

### Prerequisites
- [ ] Firebase project created
- [ ] Firestore enabled
- [ ] Authentication enabled
- [ ] Cloud Storage enabled
- [ ] Service account key downloaded
- [ ] Environment configured

### Phase 1: Foundation ✅
- [x] Firebase configuration
- [ ] Base repository pattern

### Phase 2: Repositories
- [ ] User repository
- [ ] Family tree repository
- [ ] Person repository
- [ ] Relationship repository
- [ ] File repository

### Phase 3: Services
- [ ] Family tree service
- [ ] Person service
- [ ] Relationship service
- [ ] File service

### Phase 4: Authentication
- [ ] Firebase auth integration
- [ ] Clean up old models

### Phase 5: API Endpoints
- [ ] Family tree endpoints
- [ ] People endpoints
- [ ] Relationship endpoints
- [ ] File endpoints

### Phase 6: Application
- [ ] Main application cleanup
- [ ] Schema updates

### Phase 7: Testing
- [ ] Repository tests
- [ ] Service tests
- [ ] API tests

---

## 🎯 Success Criteria

### Functional Requirements
- [ ] Users can authenticate with Firebase
- [ ] Users can create and manage family trees
- [ ] Users can add people with biographical data
- [ ] Users can create family_line and partner relationships
- [ ] Users can upload and manage files
- [ ] System calculates astrology compatibility
- [ ] React Flow visualization works with new data
- [ ] All original features preserved

### Technical Requirements
- [ ] All code uses Firestore (no SQL)
- [ ] Firebase Auth integration complete
- [ ] Google Cloud Storage for files
- [ ] Clean repository pattern
- [ ] Comprehensive error handling
- [ ] Complete test coverage
- [ ] Production-ready deployment

### Performance Requirements
- [ ] Family tree loads in <2 seconds
- [ ] Relationship queries efficient
- [ ] File uploads work smoothly
- [ ] Graph generation fast
- [ ] Stays within free tier limits

---

## 🚨 Risk Mitigation

### Technical Risks
- **Firestore query limitations**: Use denormalization and composite indexes
- **Free tier limits**: Monitor usage, implement efficient queries
- **Authentication complexity**: Use Firebase SDK best practices

### Development Risks
- **Scope creep**: Stick to feature parity first
- **Over-engineering**: Keep it simple, add complexity later
- **Testing gaps**: Write tests alongside implementation

---

## 📞 Support and Resources

### Documentation
- [Firestore Documentation](https://firebase.google.com/docs/firestore)
- [Firebase Auth Documentation](https://firebase.google.com/docs/auth)
- [Google Cloud Storage Documentation](https://cloud.google.com/storage/docs)

### Testing Tools
- Firebase Emulator Suite for local testing
- Firestore security rules testing
- pytest for Python testing

### Monitoring
- Firebase Console for usage monitoring
- Google Cloud Console for storage monitoring
- Application logs for error tracking

---

**Next Step**: Complete Task 1.2 - Base Repository Pattern