# Source Documentation for Project_Name

Document Author: [chabuuu](https://github.com/chabuuuu)

Document Version: 1.0.0 (03/04/2025)

Table of Contents:

- [Source Documentation for vmm.banking.user-service](#source-documentation-for-vmmbankinguser-service)
  - [1. Project Structure](#1-project-structure)
  - [2. Model Structure](#2-model-structure)
  - [3. Naming Convention](#3-naming-convention)
    - [3.1 General Naming Convention](#31-general-naming-convention)
    - [3.1 Enum Naming Convention](#31-enum-naming-convention)
    - [3.2 Class Naming Convention](#32-class-naming-convention)
  - [4. Exception Handling](#4-exception-handling)
    - [4.1. Create a new exception](#41-create-a-new-exception)
    - [4.2 Throw exception](#42-throw-exception)
  - [5. Security](#5-security)
    - [5.1 Generate JWT Token](#51-generate-jwt-token)
    - [5.2 Get and validate JWT Token](#52-get-and-validate-jwt-token)
  - [6. API Convention](#6-api-convention)
    - [6.1 API Versioning](#61-api-versioning)
    - [6.2 API Naming Convention](#62-api-naming-convention)
    - [6.3 How to create a response](#63-how-to-create-a-response)
  - [7. API Documentation (Swagger)](#7-api-documentation-swagger)
    - [7.1 How to documentation a API](#71-how-to-documentation-a-api)
      - [7.1.1. Exception](#711-exception)
      - [7.1.1. Validate Error](#711-validate-error)
  - [8. Workflow](#8-workflow)
  - [9. Commit convention](#9-commit-convention)
    - [9.1. Commit Message Format](#91-commit-message-format)
    - [9.2. Type](#92-type)
  - [10. Configurations](#10-configurations)
  - [11. Database migrations (Only apply when project currently in release stage)](#11-database-migrations-only-apply-when-project-currently-in-release-stage)
    - [**1. Creating a Migration File**](#1-creating-a-migration-file)
    - [**`<action>` can be:**](#action-can-be)
    - [**`<items>` represent the elements affected by the action**](#items-represent-the-elements-affected-by-the-action)
    - [**`<table>` is the affected table (if applicable).**](#table-is-the-affected-table-if-applicable)
    - [**`<version>` is an incrementing number representing the migration version.**](#version-is-an-incrementing-number-representing-the-migration-version)
      - [**Example:**](#example)
    - [**2. Creating a Rollback File**](#2-creating-a-rollback-file)
    - [4. \*\* Create Migration Logs\*\*](#4--create-migration-logs)
  - [12. Testing](#12-testing)
    - [12.1 Unit Testing](#121-unit-testing)
    - [12.2 Integration Testing](#122-integration-testing)
    - [12.3 Run test](#123-run-test)
  - [13. Specifications](#13-specifications)

## 1. Project Structure

The project is organized following the standard structure of a Spring Boot application. Below is a detailed description:

```
src/
├── main/
│ ├── java.com.kltn.livability_score.user_service/
│ │ ├── annotations/ # Custom annotations
│ │ ├── constants/ # Constants and enums
│ │ ├── consumers/ # Message consumers (e.g., Kafka, RabbitMQ)
│ │ ├── controllers/ # REST API controllers
│ │ ├── converters/ # Data converters
│ │ ├── entity/ # JPA entities
│ │ ├── exception/ # Custom exception handling
│ │ ├── model/ # Data models (VOs, DTOs, etc.)
│ │ ├── repository/ # JPA repositories
│ │ ├── security/ # Security-related classes
│ │ ├── services/ # Service interfaces and implementations
│ │ ├── specifications/ # JPA specifications for queries
│ │ └── utils/ # Utility classes
│ └── resources/
│ ├── application.properties # Common application properties
│ ├── application-dev.properties # Development-specific properties
│ └── application-prod.properties # Production-specific properties
└── test.java.com.kltn.livability_score.user_service # Unit and integration tests
```

Key Directories

- annotations/: Contains custom annotations, e.g., EnumValidator.

- constants/: Contains constants and enums used across the project.

- controllers/: Contains REST Controller classes to handle HTTP requests.

- services/: Contains service interfaces and their implementations.

- repository/: Contains JPA Repository interfaces for database queries.

- utils/: Contains utility classes such as SecurityUtil, PageUtil, and PasswordUtil.

- exception/: Contains custom exception handling classes.

- model/: Contains data model classes like VO (Value Object), DTO (Data Transfer Object), Request and Response Class.

- entity/: Contains JPA entity classes that map to database tables.

- consumers/: Contains message consumers for message brokers like Kafka or RabbitMQ.

- specifications/: Contains JPA specifications for complex queries.

- converters/: Contains classes for converting between different data types or formats.

- security/: Contains classes related to security, such as JWT token generation and validation.

- test/: Contains unit and integration tests for the application.

- resources/: Contains application properties files for different environments (dev, prod, etc.).

## 2. Model Structure

Each module will have their own model, ex:

Module User:

```
model/
├── user/
│ ├── request/ # Request classes for user module
│ ├── response/ # Response classes for user module
│ ├── dto/ # Data Transfer Objects for user module
│ ├── vo/ # Value Objects for user module
```

## 3. Naming Convention

### 3.1 General Naming Convention

- Method names should be in camelCase. Example: getUserById, createUser.
- Constants should be in UPPER_SNAKE_CASE. Example: MAX_RETRY_COUNT, DEFAULT_TIMEOUT.
- Package names should be in lowercase.

  Example: com.kltn.livability_score.user_service.

  If the package name is too long, we can use a short name. For example, we can use "user" instead of "user_service".

  If available, we can use the short name of the module. For example, we can use "user" instead of "user_service". Should not use "user_service" because it is too long and break the line.

- Variable names should be in camelCase. Example: userId, userName.

### 3.1 Enum Naming Convention

- Enum names should be in PascalCase.
- Enum constants should be in UPPER_SNAKE_CASE.

### 3.2 Class Naming Convention

- Class names should be in PascalCase. Example: UserService, UserController.
- Request and Response classes should be suffixed with Request or Response respectively. Example: UserRegisterRequest, UserLoginResponse.
- DTO classes should be suffixed with DTO. Example: UserDTO.
- VO classes should be suffixed with VO. Example: UserVO.
- Repository interfaces should be suffixed with Repository. Example: UserRepository.
- Service interfaces should be suffixed with Service. Example: UserService.
- Service implementation classes should be suffixed with Impl. Example: UserServiceImpl.
- Controller classes should be suffixed with Controller. Example: UserController.
- Converter classes should be suffixed with Converter. Example: UserConverter.
- Exception classes should be suffixed with Exception. Example: UserRegisterException.
- Utility classes should be suffixed with Util. Example: SecurityUtil, PageUtil, PasswordUtil.
- Test classes should be suffixed with Test. Example: UserServiceTest, UserControllerTest.
- Test classes should be in the same package as the class being tested, suffixed with Test.

## 4. Exception Handling

### 4.1. Create a new exception

Each module will have their own exception handling, ex:

Module User:

```
exception/
├── user/
│ ├── UserRegisterException.java # Custom exception for user registration
│ ├── UserLoginException.java # Custom exception for user login
│ ├── UserUpdateProfileException.java # Custom exception for user profile update
```

Each module will have many method, ex User will have many methods like register, login, update profile, etc. Each method will have their own exception class. For example, UserRegisterException.java will handle exceptions related to user registration.

All exceptions MUST implement the base exception interface ErrorCodeType:

```java
public interface ErrorCodeType {
    String getValue();

    String getDescription();

    HttpStatus getHttpStatus();
}
```

And implement the base exception class BaseException:

```java
@AllArgsConstructor
public enum UserRegisterException implements ErrorCodeType {
    ;

    final String value;
    final String description;
    final HttpStatus httpStatus;

    @Override
    public String getValue() {
        return value;
    }

    @Override
    public String getDescription() {
        return description;
    }

    @Override
    public HttpStatus getHttpStatus() {
        return httpStatus;
    }
}
```

Next, we will create all the error code for the method Register User:

The error code will folow this format:

```
<PARENT>_<CHILD>_<DetailDescription>
```

- PARENT: The parent module name, ex: USER
- CHILD: The child module name, ex: USER_REGISTER
- DetailDescription: The detail description of the error code and MUST use camelCase, ex: USER_REGISTES_UserAlreadyExist
- The error code will be in uppercase and separated by underscore (\_).

Ex:

```java
@AllArgsConstructor
public enum UserRegisterException implements ErrorCodeType {

    /**
     * Error User register exception.
     */

    USER_REGISTES_UserAlreadyExist("USER_REGISTES_UserAlreadyExist", "Người dùng đã tồn tại", HttpStatus.BAD_REQUEST),

    ;

    final String value;
    final String description;
    final HttpStatus httpStatus;

    @Override
    public String getValue() {
        return value;
    }

    @Override
    public String getDescription() {
        return description;
    }

    @Override
    public HttpStatus getHttpStatus() {
        return httpStatus;
    }
}
```

### 4.2 Throw exception

To throw an exception, we will use the custom exception class and pass the error code and message to it. For example, in the UserServiceImpl class, we will throw the UserRegisterException like this:

```java
public void register(UserRegisterRequest request) {
    // Check if user already exists
    if (userRepository.existsByEmail(request.getEmail())) {
        throw new BaseError(UserRegisterException.USER_REGISTES_UserAlreadyExist); //Custom exception
    }
}
```

This will create the response like this:

```json
{
  "status": "400",
  "result": "Failed",
  "error": {
    "code": "USER_REGISTES_UserAlreadyExist",
    "message": "Người dùng đã tồn tại",
    "data": null
  },
  "data": null
}
```

## 5. Security

### 5.1 Generate JWT Token

- JWT Token will be used for authentication and authorization.
- JWT Token will be generated using the JWT library.

How to generate JWT Token:

```java
        var jwtTokenVo = new JwtTokenVo(
                userEntity.getId(),
                userEntity.getUsername(),
                List.of(roleEntity.getCode()), deviceId, ipAddress);
        String accessToken = SecurityUtil.createToken(jwtTokenVo);
        String refreshToken = SecurityUtil.createRefreshToken(jwtTokenVo);
```

The JwtTokenVo class will contain the following fields:

```java
public class JwtTokenVo {
    Integer userId;
    String username;
    List<String> roles;
    String deviceId;
    String ipAddress;

    public List<GrantedAuthority> getAuthorities() {
        if (roles == null)
            return new ArrayList<>();
        return roles.stream().map(s -> (GrantedAuthority) () -> s).toList();
    }
}
```

Details of the fields:\

- userId: The ID of the user.
- username: The username of the user.
- roles: The roles of the user.
- deviceId: The device ID of the user.
- ipAddress: The IP address of the user.
- getAuthorities(): The authorities of the user.

### 5.2 Get and validate JWT Token

How to get current user:

```java
JwtTokenVo currentLoggedUser = SecurityUtil.getSession();
```

This will return the current logged user.

If the request jwt token is invalid, this method also will throw the exception:

## 6. API Convention

### 6.1 API Versioning

- All APIs will be versioned using the URL path.

- The version will be in the format v1, v2, etc.

- The version will be in the URL path like this: /api/v1/user/register.

### 6.2 API Naming Convention

- All APIs will be in lowercase.
- All APIs will use hyphen (-) to separate words.
- All APIs will use POST for create, GET for read, PUT for update, DELETE for delete.
- Response field names should be in camelCase.
- Request field names should be in camelCase.
- All APIs will use the following format:

```
POST /api/v1/user/register
GET /api/v1/user/{userId}
PUT /api/v1/user/{userId}
DELETE /api/v1/user/{userId}
```

- All APIs will use the following format for query parameters:

```
GET /api/v1/user?username={username}&email={email}
```

- All APIs will use the following format for path parameters:

```
GET /api/v1/user/{userId}
```

- All APIs will use the following format for request body:

```json
POST /api/v1/user/register
{
  "username": "string",
  "password": "string",
  "email": "string"
}
```

- All APIs will use the following format for response body:

```json
{
  "status": "200",
  "result": "Succeeded",
  "error": null,
  "data": {
    "bookingType": "RAILWAY",
    "bookingId": 1,
    "userId": 1,
    "username": "string",
    "email": "string",
    "createdAt": "2023-10-01T00:00:00Z",
    "updatedAt": "2023-10-01T00:00:00Z"
  }
}
```

Explanation of the fields:

- status: The status of the response.
- result: The result of the response. (Success || Failed).
- error: The error of the response. Null if no error.
- data: The data of the response.

- All APIs will use the following format for error response body:

```json
{
  "status": "400",
  "result": "Failed",
  "error": {
    "code": "USER_REGISTES_UserAlreadyExist",
    "message": "Người dùng đã tồn tại",
    "data": null
  },
  "data": null
}
```

- All APIs will use the following format for success response body:

```json
{
  "status": "200",
  "result": "Success",
  "error": null,
  "data": {
    "userId": 1,
    "username": "string",
    "email": "string"
  }
}
```

- All APIs will use the following format for success response body with list:

```json
{
  "status": "200",
  "result": "Success",
  "error": null,
  "data": [
    {
      "userId": 1,
      "username": "string",
      "email": "string"
    },
    {
      "userId": 2,
      "username": "string",
      "email": "string"
    }
  ]
}
```

- All APIs will use the following format for success response body with pagination:

```json
{
  "status": "200",
  "result": "Succeeded",
  "error": null,
  "data": {
    "records": 5,
    "items": [
      {
        "id": 1,
        "email": "haphuthinh332004@gmail.com",
        "phoneNumber": null,
        "username": "haphuthinh",
        "roleCode": "CUSTOMER",
        "roleName": "Khách hàng"
      }
    ],
    "pages": 1,
    "page": 1,
    "record_from": 1,
    "record_to": 1
  }
}
```

Explaination of the fields:

- status: The status of the response.
- result: The result of the response.
- error: The error of the response.
- data: The data of the response.
- data.records: The total number of records. (Total number of records in the database)
- data.items: The list of items.
- data.pages: The total number of pages. (Total number of pages in the database)
- data.page: The current page.
- data.record_from: The first record of the current page.
- data.record_to: The last record of the current page.

### 6.3 How to create a response

The return type of the controller method must be:

```java
ResponseEntity<ResponseVO<YOUR_RESPONSE_TYPE>>
```

Example:

```java
@PostMapping
public ResponseEntity<ResponseVO<UserRegisterRes>> registerUser(@RequestBody @Valid UserRegisterReq request)
```

Then the response must be return like this:

```java
return ResponseEntityGenerator.okFormat(userRegisterRes);
```

Full example of register user API:

```java
@PostMapping
    public ResponseEntity<ResponseVO<UserRegisterRes>> registerUser(@RequestBody @Valid UserRegisterReq request) {

        UserRegisterRes userRegisterRes = userResgisterService.register(request);

        return ResponseEntityGenerator.okFormat(userRegisterRes);
    }
```

The ResponseEntityGenerator include these method:

- createdFormat: use for CREATE api, ex: create user, register user,...

- findManyFormat: use for FIND MANY api, ex: find all users,...

- deleteFormat: use for DELETE api, ex: delete user,...

- updateFormat: use for UPDATE api, ex: update user,...

- findOneFormat: use of FIND ONE API, ex: find user by id,...

- pagingFormat: use for any PAGING api

- okFormat: use for any API that not on any case above, this will return status 200

- find: use for any FIND API that not on any case above, this will return status 200

## 7. API Documentation (Swagger)

### 7.1 How to documentation a API

All method on controller must using:

- @Operation
- @ApiErrorResponse

Example:

```java
    @PostMapping
    @Operation(summary = "Register new user", description = "This API wil register new user account")
    @ApiErrorResponse(errorEnum = NoException.class, validateSchema = UserRegisterReq.class)
    public ResponseEntity<ResponseVO<UserRegisterRes>> registerUser(@RequestBody @Valid UserRegisterReq request) {
    }

```

Explain:

- @Operation will mark to swagger that this API must include in Swagger document, you can fill the summary, description,...

- @ApiErrorResponse will mark to swagger that this API will include some error.

There are 2 types of error:

#### 7.1.1. Exception

- Error defined in [4.1. Create a new exception](#41-create-a-new-exception) that being thrown.

  For example:

```java
errorEnum = UserRegisterException.class
```

The UserRegisterException content:

```java
public enum UserRegisterException implements ErrorCodeType {

    /**
     * Error User register exception.
     */
    USER_REGISTES_UserAlreadyExist("USER_REGISTES_UserAlreadyExist", "Người dùng đã tồn tại",
            HttpStatus.NOT_ACCEPTABLE),

    ;
}
```

This will tell Swagger that this API will have these exception in UserRegisterException being thrown.

Result:

![alt text](documents/images/Screenshot_20250403_113356.png)

#### 7.1.1. Validate Error

- Error that being throw by annotation in Request Class:

```java
@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
public class UserRegisterReq {
    @NotEmpty(message = "NOT_EMPTY")
    @Schema(description = "Username", example = "haphuthinh")
    private String username;

    @NotEmpty(message = "NOT_EMPTY_PASSWORD")
    @Size(min = 8, max = 30, message = "PASSWORD_LENGTH_INVALID")
    @Schema(description = "Password", example = "hasdjJMkc??1")
    @Pattern(regexp = "^(?=.*[A-Z])(?=.*\\d)[^\\n\\r]*$", message = "PASSWORD_INVALID_RULE")
    private String password;
}

```

Include in;

```java
    @ApiErrorResponse(validateSchema = UserRegisterReq.class)
```

This will generate:

![alt text](documents/images/Screenshot_20250403_113747.png)

## 8. Workflow

![alt text](https://images.viblo.asia/84f47fd1-a009-4beb-8957-26395fe1023d.png)

## 9. Commit convention

### 9.1. Commit Message Format

Each commit message consists of a header, a body and a footer. The header has a special format that includes a type, a scope and a subject:

```
<type>(<scope>): <subject>
<BLANK LINE>
<body>
<BLANK LINE>
<footer>
```

The header is mandatory and the scope of the header is optional.

The <type> word should be one of the rules items you have written in your .commitlintrc.json file and the <scope> is the module/component you are working on.

Samples:

```
docs(changelog): update changelog to beta.5
```

```
fix(release): need to depend on latest rxjs and zone.js

The version in our package.json gets copied to the one we publish, and users need the latest of these.
```

### 9.2. Type

Must be one of the following:

- build: Changes that affect the build system or external
- dependencies (example scopes: gulp, broccoli, npm)
- ci: Changes to our CI configuration files and scripts (example scopes: Travis, Circle, BrowserStack, SauceLabs)
- docs: Documentation only changes
- feat: A new feature
- fix: A bug fix
- perf: A code change that improves performance
- refactor: A code change that neither fixes a bug nor adds a feature
- style: Changes that do not affect the meaning of the code (white-space, formatting, missing semi-colons, etc)
- test: Adding missing tests or correcting existing tests

## 10. Configurations

Source configurations will place in: /main/resources

There are:

- application.properties: Default configuations
- application-dev.properties: Develop enviroment configurations
- application-prod.properties: Production enviroment configurations

In .env:

```.env
# This is the enviromemt of the backend
BACKEND_ENVIROMENT=dev # dev | prod
```

This will determine which enviroment configuraton will be using

## 11. Database migrations (Only apply when project currently in release stage)

### **1. Creating a Migration File**

First, create a file in the `/migrations` directory. The filename must follow this pattern:

```
V<version>__<action>--<items>--<table (if applicable)>.sql
```

### **`<action>` can be:**

- `add-column`
- `drop-column`
- `alter-column`
- `add-table`
- `drop-table`
- `add-trigger`
- `drop-trigger`

### **`<items>` represent the elements affected by the action**

For example, to add a column `order_code`:

```
V1__add-column--order_code--order.sql
```

If multiple items are involved, separate them using `&`. For example, adding `order_code` and `order_id`:

```
V1__add-column--order_code&order_id--order.sql
```

### **`<table>` is the affected table (if applicable).**

### **`<version>` is an incrementing number representing the migration version.**

#### **Example:**

To add the column `order_code` to the `order` table:

```
V1__add-column--order_code--order.sql
```

---

### **2. Creating a Rollback File**

After creating the migration file, create a corresponding rollback file in the `./rollbacks` directory. The filename must follow this pattern:

```
R<version>__<action>_<items>_<table (if applicable)>.sql
```

The `<action>, <version>, <items>, <table>` follow the same rules as migration files.

For example, if the migration file is:

```
V1__add-column--order_code--order.sql
```

which adds the column `order_code` to the `order` table,  
then the rollback file should **remove** that column:

```
R1__drop-column--order_code--order.sql
```

---

### 4. ** Create Migration Logs**

Remember to create new version on `migration_history` table.

## 12. Testing

### 12.1 Unit Testing

- Unit tests are located in the `src/test/java` directory.
- Each module has its own test directory.
- The test classes are suffixed with `Test`.
- The test classes are in the same package as the class being tested.

Example:

```java
@ExtendWith(MockitoExtension.class)
class UserServiceTest {

    @Mock
    private UserRepository userRepository;

    @InjectMocks
    private UserServiceImpl userService;

    @Test
    void testGetUserById() {
        // Giả lập dữ liệu
        UserEntity mockUser = new UserEntity(1, "John_Doe", "password123");
        when(userRepository.findById(1)).thenReturn(Optional.of(mockUser));

        // Gọi service
        UserEntity user = userService.getUserById(1);

        // Kiểm tra kết quả
        assertNotNull(user);
        assertEquals("John_Doe", user.getUsername());
    }
}
```

Note: Each function should have at least 1 test case.

### 12.2 Integration Testing

- Integration tests are located in the `src/test/java` directory.
- Each module has its own test directory.
- The test classes are suffixed with `IT` or `IntegrationTest`.
- The test classes are in the same package as the class being tested.
- Integration tests should use the `@SpringBootTest` annotation to load the application context.
- Use `@TestPropertySource` to specify test properties.
- Use `@AutoConfigureMockMvc` to configure the MockMvc instance for testing REST APIs.
- Use `@Rollback` to rollback the database changes after each test.
- Use `@Transactional` to ensure that each test runs in a transaction.
- Use `@DirtiesContext` to reset the application context after each test.

Example:

We want to test the `UserController` class:

```java
@RestController
@RequestMapping("/users")
public class UserController {
    private final UserService userService;

    public UserController(UserService userService) {
        this.userService = userService;
    }

    @GetMapping("/{id}")
    public ResponseEntity<User> getUserById(@PathVariable Long id) {
        return ResponseEntity.ok(userService.getUserById(id));
    }
}

```

Then we will create a test class like this:

```java
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@AutoConfigureMockMvc
class UserControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private UserService userService;

    @Test
    void testGetUserById() throws Exception {
        User mockUser = new User(1L, "John Doe");
        when(userService.getUserById(1L)).thenReturn(mockUser);

        mockMvc.perform(get("/users/1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.name").value("John Doe"));
    }
}

```

### 12.3 Run test

- To run all tests, use the following command:

```bash
mvn test
```

The test results will be displayed in the console and in directory `target/surefire-reports`.

## 13. Specifications

- All specifications will be in the `specifications` package.

Example:

```java
public class PrescriptionSpecification {
    public static Specification<Prescription> filter(
            Integer prescriptionId,
            String patientName,
            String pharmacistName,
            String status,
            String fromDate,
            String toDate
    ) {
        return (root, query, builder) -> {
            return builder.and(
                    prescriptionId == null ? builder.conjunction() : builder.equal(root.get("id"), prescriptionId),

                    //Get patient name by join to serviceRecord, then get patient
                    patientName == null ? builder.conjunction() : builder.like(root.get("serviceRecord").get("patient").get("fullname"), "%" + patientName + "%"),
                    pharmacistName == null ? builder.conjunction() : builder.like(root.get("pharmacist").get("fullname"), "%" + pharmacistName + "%"),
                    status == null ? builder.conjunction() : builder.equal(root.get("status"), status),
                    fromDate == null ? builder.conjunction() : builder.greaterThanOrEqualTo(root.get("createAt"), fromDate),
                    toDate == null ? builder.conjunction() : builder.lessThanOrEqualTo(root.get("createAt"), toDate),

                    //deleteAt is null
                    builder.isNull(root.get("deleteAt"))
            );
        };
    }
}
```

Using in service:

```java
        Specification<Prescription> specification = PrescriptionSpecification.filter(prescriptionId, patientName,
                pharmacistName, status, fromDate, toDate);

        Page<Prescription> prescriptionPage = prescriptionRepository.findAll(specification, pageable);
```
# spring-boot-base-source
# kltn-livability-score-backend
