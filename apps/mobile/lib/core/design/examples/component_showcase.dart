import 'package:flutter/material.dart';
import 'package:praxis_shared/praxis_shared.dart';

import '../design_system.dart';

/// Mobile component showcase for visual reference in debug mode.
class ComponentShowcase extends StatelessWidget {
  const ComponentShowcase({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Component Showcase')),
      body: ListView(
        padding: MobileSpacing.pagePadding,
        children: [
          // Buttons
          Text('Buttons', style: theme.textTheme.headlineSmall),
          const SizedBox(height: MobileSpacing.md),
          AppButton(label: 'Primary', onPressed: () {}),
          const SizedBox(height: MobileSpacing.sm),
          AppButton(label: 'Destructive', isDestructive: true, onPressed: () {}),
          const SizedBox(height: MobileSpacing.sm),
          const AppButton(label: 'Loading', isLoading: true),
          const SizedBox(height: MobileSpacing.sm),
          const AppButton(label: 'Disabled'),
          const SizedBox(height: MobileSpacing.sm),
          AppButton(label: 'With Icon', icon: Icons.add, onPressed: () {}),
          const Divider(height: MobileSpacing.xl),

          // Cards
          Text('Cards', style: theme.textTheme.headlineSmall),
          const SizedBox(height: MobileSpacing.md),
          const AppCard(child: Text('Simple card')),
          const SizedBox(height: MobileSpacing.sm),
          const AppCard(title: 'Card with Header', child: Text('Card content here.')),
          const Divider(height: MobileSpacing.xl),

          // Inputs
          Text('Inputs', style: theme.textTheme.headlineSmall),
          const SizedBox(height: MobileSpacing.md),
          const AppInput(label: 'Email', hint: 'user@example.com'),
          const SizedBox(height: MobileSpacing.sm),
          const AppInput(label: 'Password', obscureText: true),
          const SizedBox(height: MobileSpacing.sm),
          const AppInput(label: 'Error', errorText: 'Required field'),
          const Divider(height: MobileSpacing.xl),

          // Badges
          Text('Badges', style: theme.textTheme.headlineSmall),
          const SizedBox(height: MobileSpacing.md),
          const Wrap(
            spacing: MobileSpacing.sm,
            children: [
              AppBadge(text: 'Info', variant: AppBadgeVariant.info),
              AppBadge(text: 'Success', variant: AppBadgeVariant.success),
              AppBadge(text: 'Warning', variant: AppBadgeVariant.warning),
              AppBadge(text: 'Error', variant: AppBadgeVariant.error),
              AppBadge(text: 'Neutral'),
            ],
          ),
          const SizedBox(height: MobileSpacing.sm),
          const Wrap(
            spacing: MobileSpacing.sm,
            children: [
              SessionStatusBadge(status: SessionStatus.active),
              SessionStatusBadge(status: SessionStatus.paused),
              SessionStatusBadge(status: SessionStatus.ended),
            ],
          ),
          const Divider(height: MobileSpacing.xl),

          // List tiles
          Text('List Tiles', style: theme.textTheme.headlineSmall),
          const SizedBox(height: MobileSpacing.md),
          const AppListTile(title: 'Session: API Redesign', subtitle: 'COC domain'),
          const AppListTile(
            title: 'Deploy to staging',
            subtitle: 'Operational constraint',
            trailing: HeldActionStatusBadge(status: HeldActionStatus.pending),
          ),
          const Divider(height: MobileSpacing.xl),

          // Constraint gauges
          Text('Constraint Gauges', style: theme.textTheme.headlineSmall),
          const SizedBox(height: MobileSpacing.md),
          const ConstraintGauge(label: 'Financial', value: 0.3, color: PraxisColors.constraintFinancial),
          const SizedBox(height: MobileSpacing.sm),
          const ConstraintGauge(label: 'Operational', value: 0.6, color: PraxisColors.constraintOperational),
          const SizedBox(height: MobileSpacing.sm),
          const ConstraintGauge(label: 'Temporal', value: 0.85, color: PraxisColors.constraintTemporal),
          const SizedBox(height: MobileSpacing.sm),
          const ConstraintGauge(label: 'Data Access', value: 0.95, color: PraxisColors.constraintDataAccess),
          const SizedBox(height: MobileSpacing.sm),
          const ConstraintGauge(label: 'Communication', value: 0.1, color: PraxisColors.constraintCommunication),
          const Divider(height: MobileSpacing.xl),

          // Loading
          Text('Loading', style: theme.textTheme.headlineSmall),
          const SizedBox(height: MobileSpacing.md),
          const AppLoading(count: 3),
          const Divider(height: MobileSpacing.xl),

          // Color palette
          Text('Trust Colors', style: theme.textTheme.headlineSmall),
          const SizedBox(height: MobileSpacing.md),
          Wrap(
            spacing: MobileSpacing.sm,
            runSpacing: MobileSpacing.sm,
            children: [
              _swatch('Healthy', PraxisColors.trustHealthy),
              _swatch('Caution', PraxisColors.trustCaution),
              _swatch('Warning', PraxisColors.trustWarning),
              _swatch('Violation', PraxisColors.trustViolation),
              _swatch('Held', PraxisColors.trustHeld),
            ],
          ),
          const SizedBox(height: MobileSpacing.xl),
        ],
      ),
    );
  }

  static Widget _swatch(String label, Color color) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 40,
          height: 40,
          decoration: BoxDecoration(
            color: color,
            borderRadius: BorderRadius.circular(8),
          ),
        ),
        const SizedBox(height: 4),
        Text(label, style: const TextStyle(fontSize: 10)),
      ],
    );
  }
}
