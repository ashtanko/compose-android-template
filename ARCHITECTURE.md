# Architecture

This template uses feature-first Clean Architecture with MVVM and the Repository pattern. Gradle
modules enforce the important dependency rules so that architectural boundaries remain visible to
the compiler.

## Dependency direction

```text
                         ┌─────────────────────────────┐
                         │ app                         │
                         │ composition root, Hilt,     │
                         │ Navigation 3, app theme     │
                         └──────────────┬──────────────┘
                                        │
                          ┌─────────────┴─────────────┐
                          │                           │
                          ▼                           ▼
              ┌─────────────────────┐     ┌─────────────────────┐
              │ presentation        │     │ data                │
              │ Compose + ViewModel │     │ repositories, API,  │
              │ depends on domain   │     │ cache, DTO mapping  │
              └──────────┬──────────┘     └──────────┬──────────┘
                         │                           │
                         └─────────────┬─────────────┘
                                       ▼
                            ┌─────────────────────┐
                            │ domain              │
                            │ models, use cases,  │
                            │ repository contracts│
                            └─────────────────────┘
```

The feature dependency rules are:

- `domain` is a Kotlin/JVM module. It has no Android, Compose, Retrofit, serialization, or Hilt
  dependency.
- `data` depends on `domain`. It never depends on `presentation` or `app`.
- `presentation` depends on `domain`. It never depends on the concrete data implementation.
- `app` is the composition root and depends on both `data` and `presentation`, allowing Hilt to
  connect the domain repository interface to the data implementation.
- Cross-feature dependencies are not allowed by default. Move genuinely shared behavior to an
  appropriate `core` or Kotlin/JVM module.

## Layer responsibilities

### Presentation

Presentation owns Android UI concerns:

- Compose routes and screens;
- ViewModels and lifecycle-owned coroutine launches;
- sealed UI-state models and UI-specific models;
- conversion from domain failures to localized UI messages;
- intent-style callbacks such as retry and load more.

A route may obtain a ViewModel, collect `StateFlow` with lifecycle awareness, and handle imperative
effects. A plain screen receives immutable state and callbacks and must not know about Hilt,
repositories, navigation, or Flow collection.

### Domain

Domain owns application business contracts:

- entities and value models;
- use cases/interactors;
- repository interfaces;
- framework-independent success and failure models.

Domain code exposes suspending APIs but owns no `CoroutineScope`. The caller chooses the lifecycle.
Exceptions from infrastructure do not cross this boundary.

### Data

Data owns implementation details:

- repository implementations;
- remote and local data sources;
- Retrofit APIs and transport DTOs;
- DTO-to-domain mappers;
- cache and error translation policy;
- Hilt bindings for data implementations.

Server responses are untrusted input. DTOs are decoded in data and mapped before crossing the
domain boundary. The demo uses HTTPS and does not embed an API credential.

## Package and directory conventions

Source directories mirror Kotlin packages. Do not place all classes at a layer's package root.
Use the smallest meaningful subpackage from the following convention:

- `domain/model` for domain models, `domain/repository` for repository interfaces,
  `domain/result` for domain result/failure types, and `domain/usecase` for interactors;
- `data/di` for dependency-injection modules, `data/local` and `data/remote` for data sources,
  `data/remote/api` for service contracts, `data/remote/dto` for transport models, `data/mapper`
  for boundary mapping, `data/model` for data-only request/cache models, and `data/repository` for
  repository implementations;
- `presentation/di` for presentation-layer dependency injection and `presentation/ui` for routes,
  screens, ViewModels, and sealed UI state;
- `presentation/ui/model` for display-only models and `presentation/ui/components` for
  feature-local reusable composables.

Single-module UI features use the same UI convention directly under the feature package:
`ui`, `ui/model`, and `ui/components`. Composables shared across unrelated features belong in
`core/designsystem`, not in another feature's `ui/components`.

## Visibility and module API

Kotlin's implicit `public` default is not allowed in modules with intentional feature or layer
boundaries. These modules currently apply the `androidlab.kotlin.explicit-visibility` convention:

- `:feature:database`;
- `:feature:home`;
- `:feature:posts:domain`;
- `:feature:posts:data`;
- `:feature:posts:presentation`.

The convention enables the custom Detekt `architecture:ExplicitVisibility` rule for all source
sets. Non-local classes and objects, named functions, properties, and primary-constructor
properties must declare `public`, `internal`, `private`, or `protected`. The standard
`./gradlew detekt` task reports omissions as build failures, and `make verify` runs that task in
local and pull-request CI.

Use the narrowest modifier supported by actual call sites:

- `private` for file/class implementation details;
- `internal` for DTOs, data sources, repository implementations, ViewModels, UI state, screens,
  feature-local components, and DI wiring used only within one module;
- `public` for cross-module domain contracts/models/use cases and app-facing feature entry points;
- `protected` only for deliberate subclass APIs.

An explicitly public override inside an internal implementation does not expose that class. For
Compose, keep the route called by `app` public and place its internal ViewModel parameter on an
internal overload. Apply the convention to another module only after reviewing its complete API
surface; the initial scope is intentionally narrower than the whole repository.

## Posts demo feature

The posts feature loads pages from the JSONPlaceholder `/posts` REST endpoint. The remote source
uses `_page` and `_limit`, derives the next page from `X-Total-Count`, and caches successful pages in
a thread-safe in-memory local source. On a remote failure the repository returns the matching
cached page when available; otherwise it maps the failure to a domain error.

### Exact folder structure

```text
feature/posts/
├── domain/
│   ├── build.gradle.kts
│   └── src/
│       ├── main/kotlin/app/template/feature/posts/domain/
│       │   ├── model/
│       │   │   ├── Post.kt
│       │   │   └── PostsPage.kt
│       │   ├── repository/
│       │   │   └── PostsRepository.kt
│       │   ├── result/
│       │   │   └── DomainResult.kt
│       │   └── usecase/
│       │       └── GetPostsPageUseCase.kt
│       └── test/kotlin/app/template/feature/posts/domain/usecase/
│           └── GetPostsPageUseCaseTest.kt
├── data/
│   ├── build.gradle.kts
│   └── src/
│       ├── main/kotlin/app/template/feature/posts/data/
│       │   ├── di/
│       │   │   ├── PostsDataModule.kt
│       │   │   └── PostsNetworkModule.kt
│       │   ├── local/
│       │   │   └── PostsLocalDataSource.kt
│       │   ├── mapper/
│       │   │   └── PostMapper.kt
│       │   ├── model/
│       │   │   └── PostsDataPage.kt
│       │   ├── remote/
│       │   │   ├── api/
│       │   │   │   └── PostsApi.kt
│       │   │   ├── dto/
│       │   │   │   └── PostDto.kt
│       │   │   └── PostsRemoteDataSource.kt
│       │   └── repository/
│       │       └── PostsRepositoryImpl.kt
│       └── test/kotlin/app/template/feature/posts/data/
│           ├── mapper/
│           │   └── PostMapperTest.kt
│           └── repository/
│               └── PostsRepositoryImplTest.kt
└── presentation/
    ├── build.gradle.kts
    ├── consumer-rules.pro
    ├── proguard-rules.pro
    └── src/
        ├── main/
        │   ├── AndroidManifest.xml
        │   ├── kotlin/app/template/feature/posts/presentation/
        │   │   ├── di/
        │   │   │   └── PostsPresentationModule.kt
        │   │   └── ui/
        │   │       ├── components/
        │   │       │   ├── PostCard.kt
        │   │       │   ├── PostsFeedback.kt
        │   │       │   └── PostsList.kt
        │   │       ├── model/
        │   │       │   └── PostUiModel.kt
        │   │       ├── PostsRoute.kt
        │   │       ├── PostsScreen.kt
        │   │       ├── PostsUiState.kt
        │   │       └── PostsViewModel.kt
        │   └── res/values/strings.xml
        ├── test/kotlin/app/template/feature/posts/presentation/ui/
        │   └── PostsViewModelTest.kt
        └── androidTest/kotlin/app/template/feature/posts/presentation/ui/
            └── PostsScreenTest.kt
```

The existing single-module home feature follows the same presentation layout:

```text
feature/home/src/
├── main/kotlin/app/template/feature/home/ui/
│   ├── components/
│   │   └── HomeContent.kt
│   ├── model/
│   │   └── HomeUiState.kt
│   ├── HomeRoute.kt
│   ├── HomeScreen.kt
│   └── HomeViewModel.kt
├── test/kotlin/app/template/feature/home/ui/
│   └── HomeViewModelTest.kt
└── androidTest/kotlin/app/template/feature/home/ui/
    └── HomeScreenTest.kt
```

### End-to-end data flow

1. `PostsRoute` obtains `PostsViewModel`, collects its `StateFlow` with lifecycle awareness, and
   explicitly signals the idempotent initial load.
2. `PostsViewModel` launches from `viewModelScope` and invokes `GetPostsPageUseCase`.
3. The use case validates the page request and calls the domain `PostsRepository` contract.
4. Hilt resolves that contract to `PostsRepositoryImpl`.
5. The repository requests `PostDto` values from `RetrofitPostsRemoteDataSource`.
6. A successful page is cached by `InMemoryPostsLocalDataSource`, mapped to domain `Post` values,
   and returned as `DomainResult.Success`.
7. Cancellation is rethrown. Network, HTTP, and payload failures become `PostsFailure` values after
   the repository checks the cache.
8. The ViewModel maps domain models to `PostUiModel` and domain failures to `PostsErrorMessage`,
   then atomically updates `PostsUiState`.
9. `PostsScreen` renders loading, success, empty, initial error, loading-more, and append-error
   branches using state and callbacks only.

## UI state and event guidelines

Screen state is a closed, explicit model:

```kotlin
internal sealed interface PostsUiState {
    public data object Loading : PostsUiState
    public data class Success(/* immutable display data */) : PostsUiState
    public data class Error(public val message: PostsErrorMessage) : PostsUiState
}
```

- ViewModels expose read-only `StateFlow`; mutable flows remain private.
- Use `MutableStateFlow.update` for state transitions. Keep update blocks fast, pure, and free of
  network, disk, logging, clock, or random work.
- Use immutable UI data at Compose boundaries.
- Initial loading, content, empty, and error conditions must be real states, not fake domain
  sentinel values.
- Preserve existing content when pagination fails. The posts success state carries an append error
  instead of replacing the whole screen with an initial error.
- Collect state in the route with `collectAsStateWithLifecycle`; pass plain values and callbacks to
  the screen.
- Immediate user navigation remains a callback to the application host.
- Add an event stream only for asynchronous imperative effects. Use a deliberately configured
  `SharedFlow` for broadcast semantics or a buffered channel exposed as `Flow` for one UI consumer.
  Durable outcomes belong in state or persistence.

## Error and coroutine policy

- Repositories, use cases, and data sources expose `suspend` functions and do not store a
  `CoroutineScope`.
- ViewModels translate non-suspending UI callbacks into work launched in `viewModelScope`.
- Broad exception handling around suspend calls must rethrow cancellation before mapping ordinary
  failures.
- The data layer maps infrastructure exceptions to domain failures. Presentation never branches on
  `IOException`, Retrofit response types, or serialization exceptions.
- User-facing text lives in Android resources and is selected in presentation.

## Dependency injection

`App` is the `@HiltAndroidApp` application and `MainActivity` is an `@AndroidEntryPoint`.
`PostsDataModule` binds remote/local sources and `PostsRepositoryImpl` in `SingletonComponent`.
`PostsNetworkModule` provides JSON, OkHttp, Retrofit, and `PostsApi`. `PostsPresentationModule`
provides `GetPostsPageUseCase` in `ViewModelComponent`, and Hilt constructs `PostsViewModel`.

The domain module intentionally contains no injection annotations.

## Testing strategy

- Domain tests verify use-case validation and repository delegation without Android.
- Data tests verify DTO mapping, caching, error mapping, and cancellation propagation with fakes.
- ViewModel tests verify complete loading, retry, pagination, and append-error state transitions
  with coroutine test dispatchers.
- Compose tests exercise the plain `PostsScreen` with immutable states and assert visible semantics
  and callback forwarding.
- Application navigation tests replace the posts content with a deterministic test composable, so
  navigation tests never depend on the network or the Hilt graph.

Run the narrow module tests first, then use the validation matrix in
[`.agents/reference/commands.md`](.agents/reference/commands.md).
