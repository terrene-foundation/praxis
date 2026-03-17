// Shared code for Praxis desktop and mobile applications.
//
// This package contains the API client, data models, WebSocket service,
// and core authentication logic used by both the desktop and mobile apps.

// Models
export 'src/models/session.dart';
export 'src/models/constraint_set.dart';
export 'src/models/held_action.dart';
export 'src/models/delegation.dart';
export 'src/models/user.dart';
export 'src/models/trust_entry.dart';
export 'src/models/deliberation_record.dart';
export 'src/models/api_config.dart';

// API
export 'src/api/praxis_client.dart';
export 'src/api/praxis_api_exception.dart';
export 'src/api/endpoints/session_api.dart';
export 'src/api/endpoints/constraint_api.dart';
export 'src/api/endpoints/approval_api.dart';
export 'src/api/endpoints/trust_api.dart';
export 'src/api/endpoints/delegation_api.dart';
export 'src/api/endpoints/auth_api.dart';
export 'src/api/interceptors/auth_interceptor.dart';
export 'src/api/interceptors/error_interceptor.dart';
export 'src/api/interceptors/retry_interceptor.dart';

// Services
export 'src/services/websocket_service.dart';
export 'src/services/websocket_events.dart';
export 'src/services/reconnection_strategy.dart';

// Auth
export 'src/auth/auth_service.dart';
export 'src/auth/auth_state.dart';
export 'src/auth/token_provider.dart';
export 'src/auth/token_storage.dart';

// Providers
export 'src/providers/api_providers.dart';
