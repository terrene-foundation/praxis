import 'package:freezed_annotation/freezed_annotation.dart';

part 'user.freezed.dart';
part 'user.g.dart';

/// Roles available within Praxis.
enum UserRole {
  @JsonValue('supervisor')
  supervisor,
  @JsonValue('collaborator')
  collaborator,
  @JsonValue('observer')
  observer,
}

/// A Praxis user account.
@freezed
class User with _$User {
  const factory User({
    required String id,
    required String email,
    required String displayName,
    required UserRole role,
    String? avatarUrl,
  }) = _User;

  factory User.fromJson(Map<String, dynamic> json) => _$UserFromJson(json);
}
