/**
 * Spiro Design System — Button (v0.4)
 *
 * Accessible by default (keyboard, focus ring, disabled/aria handling).
 * Styled via the CSS variables defined in tokens/tokens.css — import
 * tokens.css and Button.css alongside this component, or inline the
 * Button styles into your global stylesheet.
 *
 * v0.4 changes
 *   • Pill-shaped across the board (border-radius: 9999px).
 *   • Six variants: primary, secondary, ghost, destructive, dark, light.
 *   • Three sizes: sm (32) / md (40) / lg (48) with 14 / 16 / 20 labels.
 *   • Success is a TRANSIENT state, not a variant — drive it with the
 *     `success` boolean (component flashes emerald + ✓ then reverts).
 *   • Volt still does not appear as a button colour.
 *
 * Variants
 *   primary      — Brand Blue CTA (dominant call-to-action)
 *   secondary    — Neutral bordered (pairs with primary)
 *   ghost        — Transparent (dense UI, toolbars, inline actions)
 *   destructive  — Danger (irreversible actions)
 *   dark         — Navy-filled (use on cream / periwinkle / peach sections
 *                  where Brand Blue would clash — e.g. editorial hero)
 *   light        — Cream-filled (use on navy / dark hero sections where
 *                  Brand Blue would clash with its background)
 *
 * States
 *   hover / active / focus-visible / disabled / loading / success
 *   — loading shows a spinner and sets aria-busy
 *   — success flashes emerald with a ✓ for ~1.4s, then reverts
 */

import * as React from 'react';

export type ButtonVariant =
  | 'primary'
  | 'secondary'
  | 'ghost'
  | 'destructive'
  | 'dark'
  | 'light';

export type ButtonSize = 'sm' | 'md' | 'lg';

export interface ButtonProps
  extends Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, 'disabled'> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  /** Full-width block button. */
  fullWidth?: boolean;
  /** Shows a spinner and sets aria-busy; click is suppressed. */
  loading?: boolean;
  /**
   * Transient success state — flashes emerald with a ✓ then reverts.
   * Pass `true` briefly after an action resolves; the caller is
   * responsible for flipping it back to `false` after ~1.4s, or let
   * the component auto-revert via `successDurationMs`.
   */
  success?: boolean;
  /** Auto-revert the success flash after this many ms. Default: 1400. Set to 0 to disable. */
  successDurationMs?: number;
  /** Disables the button; preferred over the native HTML `disabled` for a11y styling. */
  disabled?: boolean;
  /** Optional icon rendered before the label. */
  leadingIcon?: React.ReactNode;
  /** Optional icon rendered after the label. */
  trailingIcon?: React.ReactNode;
}

const CheckIcon: React.FC = () => (
  <svg
    viewBox="0 0 20 20"
    fill="none"
    stroke="currentColor"
    strokeWidth="2.5"
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden="true"
    focusable="false"
  >
    <polyline points="4 10.5 8.5 15 16 6" />
  </svg>
);

/**
 * Spiro Button.
 *
 * @example
 *   <Button variant="primary" size="md">Save changes</Button>
 *   <Button variant="secondary" leadingIcon={<PlusIcon />}>New project</Button>
 *   <Button variant="destructive" loading>Deleting…</Button>
 *   <Button variant="dark">Read the story</Button>
 *   <Button variant="light">Learn more</Button>
 *
 *   // transient success flash (auto-reverts after 1.4s)
 *   const [ok, setOk] = useState(false);
 *   <Button success={ok} onClick={async () => { await save(); setOk(true); }}>
 *     Save
 *   </Button>
 */
export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  function Button(
    {
      variant = 'primary',
      size = 'md',
      fullWidth = false,
      loading = false,
      success = false,
      successDurationMs = 1400,
      disabled = false,
      leadingIcon,
      trailingIcon,
      children,
      className,
      type = 'button',
      onClick,
      ...rest
    },
    ref
  ) {
    // Internal echo of the `success` prop — lets us auto-revert after
    // successDurationMs without forcing callers to own the timer.
    const [flash, setFlash] = React.useState(false);

    React.useEffect(() => {
      if (!success) {
        setFlash(false);
        return;
      }
      setFlash(true);
      if (successDurationMs <= 0) return;
      const t = window.setTimeout(() => setFlash(false), successDurationMs);
      return () => window.clearTimeout(t);
    }, [success, successDurationMs]);

    const classes = [
      'spiro-btn',
      `spiro-btn--${variant}`,
      `spiro-btn--${size}`,
      fullWidth && 'spiro-btn--full',
      loading && 'spiro-btn--loading',
      flash && 'spiro-btn--success',
      className,
    ]
      .filter(Boolean)
      .join(' ');

    return (
      <button
        ref={ref}
        type={type}
        className={classes}
        disabled={disabled || loading}
        aria-busy={loading || undefined}
        aria-live={flash ? 'polite' : undefined}
        onClick={loading ? undefined : onClick}
        {...rest}
      >
        {loading ? (
          <span className="spiro-btn__spinner" aria-hidden="true" />
        ) : flash ? (
          <span className="spiro-btn__icon spiro-btn__icon--leading">
            <CheckIcon />
          </span>
        ) : (
          leadingIcon && (
            <span className="spiro-btn__icon spiro-btn__icon--leading">
              {leadingIcon}
            </span>
          )
        )}
        <span className="spiro-btn__label">{children}</span>
        {!loading && !flash && trailingIcon && (
          <span className="spiro-btn__icon spiro-btn__icon--trailing">
            {trailingIcon}
          </span>
        )}
      </button>
    );
  }
);
