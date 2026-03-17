import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:praxis_shared/praxis_shared.dart';

import '../../core/design/design_system.dart';

/// Provider to fetch a single trust entry by ID.
final _trustEntryProvider =
    FutureProvider.family<TrustEntry, String>((ref, id) async {
  final client = ref.watch(praxisClientProvider);
  return client.trust.getEntry(id);
});

/// Detail screen for a trust chain entry on mobile.
///
/// Shows full cryptographic details: hashes, signatures, signer key, parent
/// hash, and the entry payload as formatted JSON.
class TrustEntryDetailScreen extends ConsumerWidget {
  final String entryId;

  const TrustEntryDetailScreen({super.key, required this.entryId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final entryAsync = ref.watch(_trustEntryProvider(entryId));
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Trust Entry')),
      body: entryAsync.when(
        data: (entry) => SingleChildScrollView(
          padding: MobileSpacing.pagePadding,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Entry type badge row
              Row(
                children: [
                  _EntryTypePill(type: entry.type),
                  const Spacer(),
                  _VerificationBadge(status: entry.verificationStatus),
                ],
              ),
              const SizedBox(height: MobileSpacing.lg),

              // Content hash (full, with copy)
              _HashField(
                label: 'Content Hash',
                value: entry.hash,
                theme: theme,
              ),
              const SizedBox(height: MobileSpacing.md),

              // Principal
              _DetailRow(
                label: 'Signer',
                value: entry.principalName,
                theme: theme,
              ),
              const SizedBox(height: MobileSpacing.md),

              // Principal ID (key ID, with copy)
              _HashField(
                label: 'Signer Key ID',
                value: entry.principalId,
                theme: theme,
              ),
              const SizedBox(height: MobileSpacing.md),

              // Parent hash
              if (entry.parentHash != null) ...[
                _HashField(
                  label: 'Parent Hash',
                  value: entry.parentHash!,
                  theme: theme,
                ),
                const SizedBox(height: MobileSpacing.md),
              ],

              // Description
              _DetailRow(
                label: 'Description',
                value: entry.description,
                theme: theme,
              ),
              const SizedBox(height: MobileSpacing.md),

              // Timestamp
              _DetailRow(
                label: 'Timestamp',
                value: _formatTimestamp(entry.createdAt),
                theme: theme,
              ),
              const SizedBox(height: MobileSpacing.lg),

              // Payload section
              if (entry.metadata != null && entry.metadata!.isNotEmpty) ...[
                Text(
                  'Payload',
                  style: theme.textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: MobileSpacing.sm),
                Container(
                  width: double.infinity,
                  constraints: const BoxConstraints(maxHeight: 300),
                  decoration: BoxDecoration(
                    color: theme.colorScheme.surfaceContainerHighest,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: SingleChildScrollView(
                    padding: const EdgeInsets.all(MobileSpacing.sm),
                    child: Text(
                      const JsonEncoder.withIndent('  ')
                          .convert(entry.metadata),
                      style: theme.textTheme.bodySmall?.copyWith(
                        fontFamily: 'monospace',
                        fontFamilyFallback: const ['Courier'],
                        fontSize: 12,
                      ),
                    ),
                  ),
                ),
              ],

              const SizedBox(height: MobileSpacing.xl),
            ],
          ),
        ),
        loading: () => const Padding(
          padding: MobileSpacing.pagePadding,
          child: AppLoading(count: 5),
        ),
        error: (e, _) => Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.error_outline, size: 48, color: Colors.red),
              const SizedBox(height: MobileSpacing.md),
              Text('Error: $e'),
            ],
          ),
        ),
      ),
    );
  }

  String _formatTimestamp(DateTime dt) {
    final local = dt.toLocal();
    return '${local.year}-${local.month.toString().padLeft(2, '0')}-'
        '${local.day.toString().padLeft(2, '0')} '
        '${local.hour.toString().padLeft(2, '0')}:'
        '${local.minute.toString().padLeft(2, '0')}:'
        '${local.second.toString().padLeft(2, '0')}';
  }
}

/// A color-coded pill showing the trust entry type.
class _EntryTypePill extends StatelessWidget {
  final TrustEntryType type;

  const _EntryTypePill({required this.type});

  @override
  Widget build(BuildContext context) {
    final (color, label) = switch (type) {
      TrustEntryType.genesis => (Colors.blue, 'Genesis'),
      TrustEntryType.delegation => (Colors.purple, 'Delegation'),
      TrustEntryType.constraint => (Colors.orange, 'Constraint'),
      TrustEntryType.attestation => (Colors.green, 'Attestation'),
      TrustEntryType.action => (Colors.teal, 'Action'),
      TrustEntryType.approval => (Colors.indigo, 'Approval'),
    };

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: color,
          fontSize: 13,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}

/// Verification status badge.
class _VerificationBadge extends StatelessWidget {
  final VerificationStatus status;

  const _VerificationBadge({required this.status});

  @override
  Widget build(BuildContext context) {
    final (icon, color, label) = switch (status) {
      VerificationStatus.verified => (
        Icons.verified,
        PraxisColors.trustHealthy,
        'Verified',
      ),
      VerificationStatus.unverified => (
        Icons.help_outline,
        Colors.grey,
        'Unverified',
      ),
      VerificationStatus.failed => (
        Icons.error_outline,
        PraxisColors.trustViolation,
        'Failed',
      ),
    };

    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 16, color: color),
        const SizedBox(width: 4),
        Text(
          label,
          style: TextStyle(
            color: color,
            fontSize: 12,
            fontWeight: FontWeight.w500,
          ),
        ),
      ],
    );
  }
}

/// A detail row with label and value.
class _DetailRow extends StatelessWidget {
  final String label;
  final String value;
  final ThemeData theme;

  const _DetailRow({
    required this.label,
    required this.value,
    required this.theme,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: theme.textTheme.labelSmall?.copyWith(color: Colors.grey),
        ),
        const SizedBox(height: 2),
        Text(value, style: theme.textTheme.bodyMedium),
      ],
    );
  }
}

/// A hash/key field with monospace text and a copy button.
class _HashField extends StatelessWidget {
  final String label;
  final String value;
  final ThemeData theme;

  const _HashField({
    required this.label,
    required this.value,
    required this.theme,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: theme.textTheme.labelSmall?.copyWith(color: Colors.grey),
        ),
        const SizedBox(height: 2),
        Row(
          children: [
            Expanded(
              child: Text(
                value,
                style: theme.textTheme.bodySmall?.copyWith(
                  fontFamily: 'monospace',
                  fontFamilyFallback: const ['Courier'],
                  fontSize: 12,
                ),
              ),
            ),
            IconButton(
              icon: const Icon(Icons.copy, size: 16),
              visualDensity: VisualDensity.compact,
              tooltip: 'Copy to clipboard',
              onPressed: () {
                Clipboard.setData(ClipboardData(text: value));
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text('$label copied to clipboard'),
                    duration: const Duration(seconds: 2),
                  ),
                );
              },
            ),
          ],
        ),
      ],
    );
  }
}
