import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:praxis_shared/praxis_shared.dart';

import '../../../core/design/design_system.dart';

/// Bottom-of-sidebar user profile display with logout action.
class UserProfileBadge extends ConsumerWidget {
  final bool isCollapsed;

  const UserProfileBadge({super.key, required this.isCollapsed});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(currentUserProvider);
    final theme = Theme.of(context);

    if (user == null) return const SizedBox.shrink();

    final initials = user.displayName.isNotEmpty
        ? user.displayName
            .split(' ')
            .take(2)
            .map((w) => w.isNotEmpty ? w[0].toUpperCase() : '')
            .join()
        : '?';

    final avatar = CircleAvatar(
      radius: 18,
      backgroundColor: theme.colorScheme.primaryContainer,
      child: Text(
        initials,
        style: TextStyle(
          fontSize: 14,
          fontWeight: FontWeight.w600,
          color: theme.colorScheme.onPrimaryContainer,
        ),
      ),
    );

    if (isCollapsed) {
      return Padding(
        padding: const EdgeInsets.all(PraxisSpacing.md),
        child: Tooltip(
          message: '${user.displayName}\n${user.role.name}',
          child: avatar,
        ),
      );
    }

    return Padding(
      padding: const EdgeInsets.all(PraxisSpacing.md),
      child: PopupMenuButton<String>(
        offset: const Offset(0, -60),
        onSelected: (value) {
          if (value == 'logout') {
            ref.read(authNotifierProvider.notifier).logout();
          }
        },
        itemBuilder: (_) => [
          const PopupMenuItem(value: 'logout', child: Text('Log out')),
        ],
        child: Row(
          children: [
            avatar,
            const SizedBox(width: PraxisSpacing.sm),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    user.displayName,
                    style: theme.textTheme.bodySmall?.copyWith(
                      fontWeight: FontWeight.w600,
                    ),
                    overflow: TextOverflow.ellipsis,
                  ),
                  Text(
                    _roleLabel(user.role),
                    style: theme.textTheme.labelSmall?.copyWith(
                      color: theme.colorScheme.outline,
                    ),
                  ),
                ],
              ),
            ),
            Icon(
              Icons.unfold_more,
              size: 16,
              color: theme.colorScheme.outline,
            ),
          ],
        ),
      ),
    );
  }

  String _roleLabel(UserRole role) {
    return switch (role) {
      UserRole.supervisor => 'Supervisor',
      UserRole.collaborator => 'Collaborator',
      UserRole.observer => 'Observer',
    };
  }
}
