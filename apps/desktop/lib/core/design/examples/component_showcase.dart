import 'package:flutter/material.dart';
import 'package:praxis_shared/praxis_shared.dart';

import '../design_system.dart';

/// A showcase screen displaying every design system component in every variant.
///
/// Accessible in debug mode at route `/dev/showcase`.
class ComponentShowcase extends StatelessWidget {
  const ComponentShowcase({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Component Showcase')),
      body: ListView(
        padding: PraxisSpacing.pagePadding,
        children: [
          // --- Buttons ---
          Text('Buttons', style: theme.textTheme.headlineSmall),
          const SizedBox(height: PraxisSpacing.md),
          const Wrap(
            spacing: PraxisSpacing.sm,
            runSpacing: PraxisSpacing.sm,
            children: [
              AppButton(label: 'Primary', variant: AppButtonVariant.primary, onPressed: _noop),
              AppButton(label: 'Secondary', variant: AppButtonVariant.secondary, onPressed: _noop),
              AppButton(label: 'Outlined', variant: AppButtonVariant.outlined, onPressed: _noop),
              AppButton(label: 'Text', variant: AppButtonVariant.text, onPressed: _noop),
              AppButton(label: 'Destructive', variant: AppButtonVariant.destructive, onPressed: _noop),
              AppButton(label: 'Loading', variant: AppButtonVariant.primary, isLoading: true),
              AppButton(label: 'Disabled', variant: AppButtonVariant.primary),
            ],
          ),
          const SizedBox(height: PraxisSpacing.sm),
          const Wrap(
            spacing: PraxisSpacing.sm,
            runSpacing: PraxisSpacing.sm,
            children: [
              AppButton(label: 'Small', variant: AppButtonVariant.primary, size: AppButtonSize.small, onPressed: _noop),
              AppButton(label: 'Medium', variant: AppButtonVariant.primary, size: AppButtonSize.medium, onPressed: _noop),
              AppButton(label: 'Large', variant: AppButtonVariant.primary, size: AppButtonSize.large, onPressed: _noop),
              AppButton(icon: Icons.add, variant: AppButtonVariant.primary, onPressed: _noop),
              AppButton(icon: Icons.add, label: 'New Session', variant: AppButtonVariant.primary, onPressed: _noop),
            ],
          ),
          const Divider(height: PraxisSpacing.xxl),

          // --- Cards ---
          Text('Cards', style: theme.textTheme.headlineSmall),
          const SizedBox(height: PraxisSpacing.md),
          const AppCard(
            elevation: AppCardElevation.flat,
            child: Text('Flat card (no shadow)'),
          ),
          const SizedBox(height: PraxisSpacing.sm),
          const AppCard(
            elevation: AppCardElevation.raised,
            child: Text('Raised card'),
          ),
          const SizedBox(height: PraxisSpacing.sm),
          const AppCard(
            elevation: AppCardElevation.floating,
            child: Text('Floating card'),
          ),
          const SizedBox(height: PraxisSpacing.sm),
          AppCard(
            title: 'Card with Header',
            actions: [
              IconButton(icon: const Icon(Icons.more_vert), onPressed: () {}),
            ],
            child: const Text('This card has a title and an action button.'),
          ),
          const Divider(height: PraxisSpacing.xxl),

          // --- Inputs ---
          Text('Inputs', style: theme.textTheme.headlineSmall),
          const SizedBox(height: PraxisSpacing.md),
          const AppInput(label: 'Email', hint: 'user@example.com', prefixIcon: Icon(Icons.email)),
          const SizedBox(height: PraxisSpacing.sm),
          const AppInput(label: 'Password', obscureText: true, suffixIcon: Icon(Icons.visibility)),
          const SizedBox(height: PraxisSpacing.sm),
          const AppInput(label: 'Error state', errorText: 'This field is required'),
          const SizedBox(height: PraxisSpacing.sm),
          const AppInput(label: 'Disabled', enabled: false),
          const SizedBox(height: PraxisSpacing.sm),
          const AppInput(label: 'Multiline', maxLines: 3, hint: 'Enter description...'),
          const Divider(height: PraxisSpacing.xxl),

          // --- Badges ---
          Text('Badges', style: theme.textTheme.headlineSmall),
          const SizedBox(height: PraxisSpacing.md),
          const Wrap(
            spacing: PraxisSpacing.sm,
            children: [
              AppBadge(text: 'Info', variant: AppBadgeVariant.info),
              AppBadge(text: 'Success', variant: AppBadgeVariant.success),
              AppBadge(text: 'Warning', variant: AppBadgeVariant.warning),
              AppBadge(text: 'Error', variant: AppBadgeVariant.error),
              AppBadge(text: 'Neutral', variant: AppBadgeVariant.neutral),
            ],
          ),
          const SizedBox(height: PraxisSpacing.sm),
          const Wrap(
            spacing: PraxisSpacing.sm,
            children: [
              SessionStatusBadge(status: SessionStatus.active),
              SessionStatusBadge(status: SessionStatus.paused),
              SessionStatusBadge(status: SessionStatus.ended),
            ],
          ),
          const SizedBox(height: PraxisSpacing.sm),
          const Wrap(
            spacing: PraxisSpacing.sm,
            children: [
              HeldActionStatusBadge(status: HeldActionStatus.pending),
              HeldActionStatusBadge(status: HeldActionStatus.approved),
              HeldActionStatusBadge(status: HeldActionStatus.denied),
              HeldActionStatusBadge(status: HeldActionStatus.approvedWithConditions),
              HeldActionStatusBadge(status: HeldActionStatus.expired),
            ],
          ),
          const Divider(height: PraxisSpacing.xxl),

          // --- Trust indicators ---
          Text('Trust Indicators', style: theme.textTheme.headlineSmall),
          const SizedBox(height: PraxisSpacing.md),
          const Wrap(
            spacing: PraxisSpacing.lg,
            children: [
              TrustIndicator(status: VerificationStatus.verified, size: 24),
              TrustIndicator(status: VerificationStatus.unverified, size: 24),
              TrustIndicator(status: VerificationStatus.failed, size: 24),
            ],
          ),
          const Divider(height: PraxisSpacing.xxl),

          // --- Constraint gauges ---
          Text('Constraint Gauges', style: theme.textTheme.headlineSmall),
          const SizedBox(height: PraxisSpacing.md),
          const ConstraintGauge(label: 'Financial', value: 0.3, color: PraxisColors.constraintFinancial, valueLabel: '30%'),
          const SizedBox(height: PraxisSpacing.sm),
          const ConstraintGauge(label: 'Operational', value: 0.6, color: PraxisColors.constraintOperational, valueLabel: '60%'),
          const SizedBox(height: PraxisSpacing.sm),
          const ConstraintGauge(label: 'Temporal', value: 0.85, color: PraxisColors.constraintTemporal, valueLabel: '85%'),
          const SizedBox(height: PraxisSpacing.sm),
          const ConstraintGauge(label: 'Data Access', value: 0.95, color: PraxisColors.constraintDataAccess, valueLabel: '95%'),
          const SizedBox(height: PraxisSpacing.sm),
          const ConstraintGauge(label: 'Communication', value: 0.1, color: PraxisColors.constraintCommunication, valueLabel: '10%'),
          const SizedBox(height: PraxisSpacing.md),
          const ConstraintDotsIndicator(values: [0.3, 0.6, 0.85, 0.95, 0.1]),
          const Divider(height: PraxisSpacing.xxl),

          // --- Loading skeletons ---
          Text('Loading Skeletons', style: theme.textTheme.headlineSmall),
          const SizedBox(height: PraxisSpacing.md),
          const AppLoading(variant: SkeletonVariant.card),
          const SizedBox(height: PraxisSpacing.sm),
          const AppLoading(variant: SkeletonVariant.listItem, count: 3),
          const SizedBox(height: PraxisSpacing.sm),
          const AppLoading(variant: SkeletonVariant.paragraph),
          const Divider(height: PraxisSpacing.xxl),

          // --- Empty state ---
          Text('Empty State', style: theme.textTheme.headlineSmall),
          const SizedBox(height: PraxisSpacing.md),
          const SizedBox(
            height: 200,
            child: AppEmptyState(
              icon: Icons.layers_outlined,
              title: 'No Sessions',
              description: 'Create your first CO session to get started.',
              actionLabel: 'New Session',
            ),
          ),
          const Divider(height: PraxisSpacing.xxl),

          // --- Color palette ---
          Text('Trust State Colors', style: theme.textTheme.headlineSmall),
          const SizedBox(height: PraxisSpacing.md),
          Wrap(
            spacing: PraxisSpacing.sm,
            runSpacing: PraxisSpacing.sm,
            children: [
              _colorSwatch('Healthy', PraxisColors.trustHealthy),
              _colorSwatch('Caution', PraxisColors.trustCaution),
              _colorSwatch('Warning', PraxisColors.trustWarning),
              _colorSwatch('Violation', PraxisColors.trustViolation),
              _colorSwatch('Held', PraxisColors.trustHeld),
            ],
          ),
          const SizedBox(height: PraxisSpacing.md),
          Text('Constraint Dimension Colors', style: theme.textTheme.headlineSmall),
          const SizedBox(height: PraxisSpacing.md),
          Wrap(
            spacing: PraxisSpacing.sm,
            runSpacing: PraxisSpacing.sm,
            children: [
              _colorSwatch('Financial', PraxisColors.constraintFinancial),
              _colorSwatch('Operational', PraxisColors.constraintOperational),
              _colorSwatch('Temporal', PraxisColors.constraintTemporal),
              _colorSwatch('Data Access', PraxisColors.constraintDataAccess),
              _colorSwatch('Communication', PraxisColors.constraintCommunication),
            ],
          ),
          const SizedBox(height: PraxisSpacing.xxl),
        ],
      ),
    );
  }

  static Widget _colorSwatch(String label, Color color) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 48,
          height: 48,
          decoration: BoxDecoration(
            color: color,
            borderRadius: BorderRadius.circular(8),
          ),
        ),
        const SizedBox(height: 4),
        Text(label, style: const TextStyle(fontSize: 11)),
      ],
    );
  }
}

void _noop() {}
