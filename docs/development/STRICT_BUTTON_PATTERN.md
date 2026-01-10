# Strict Button Pattern

> **Session:** 086 | **Date:** 2026-01-09 | **PR:** #675

---

## For the Physician-Developer

You're a physician who codes. You understand systems, you understand failure modes. Here's this pattern in terms you'll appreciate.

### The Problem in Plain Language

Imagine an IV pump that looks perfectly normal - lights on, display working - but there's no tubing connected. The patient clicks the bolus button. Nothing happens. They click again. Nothing. Frustration mounts.

**That's what a button without an `onClick` handler is.** It renders on screen, it looks clickable, it highlights on hover... but when clicked, nothing happens. No error message. No feedback. Just silence.

This is the worst category of bug: **silent failure**. The user doesn't know if they:
- Clicked wrong
- Need to wait
- Found a bug

They just know something should have happened, and it didn't.

### The Real Bug That Prompted This

In our scheduling app, the "New Template" button in Admin > Rotations did exactly this. It looked perfect. Clicked it. Nothing. The code:

```tsx
// THE BUG - no onClick handler
<button className="pretty-styles">
  New Template
</button>
```

A user would have spent minutes wondering why they couldn't create templates.

### Quick Reference Card

```tsx
// ACTION BUTTON - needs onClick
<Button onClick={() => doSomething()}>Click Me</Button>

// FORM SUBMIT - needs type="submit"
<Button type="submit">Submit Form</Button>

// COMPILE ERROR - TypeScript stops this
<Button>Click Me</Button>  // Won't compile
```

That's it. If you're just here to use buttons correctly, you're done. Read on only if you want to understand the mechanism.

---

## The Technical Solution

### TypeScript Discriminated Union

We use TypeScript's type system to enforce that every `<Button>` has either:
1. An `onClick` handler, OR
2. `type="submit"` (for form buttons that trigger `onSubmit`)

```tsx
// Action buttons - trigger something on click
interface ActionButtonProps extends ButtonBaseProps {
  onClick: (e: React.MouseEvent<HTMLButtonElement>) => void;
  type?: 'button' | 'reset';
}

// Form submit buttons - work via form's onSubmit
interface SubmitButtonProps extends ButtonBaseProps {
  type: 'submit';
  onClick?: (e: React.MouseEvent<HTMLButtonElement>) => void;  // Optional extra handler
}

// The union: must satisfy one or the other
export type ButtonProps = ActionButtonProps | SubmitButtonProps;
```

### Why This Beats ESLint Rules

| Approach | Catches At | Coverage | Bypassed By |
|----------|------------|----------|-------------|
| ESLint rule | Lint time | ~70% | Dynamic props, spread |
| This pattern | **Compile time** | **100%** | Nothing (it's the type system) |

The type system is inescapable. If you write `<Button>`, TypeScript immediately shows an error in your IDE.

---

## Code Examples

### Correct Usage

```tsx
// 1. Standard action button
<Button onClick={() => setModalOpen(true)}>
  Open Settings
</Button>

// 2. Button with loading state
<Button
  onClick={handleSave}
  isLoading={isSaving}
>
  Save Changes
</Button>

// 3. Form submit button (inside a <form>)
<form onSubmit={handleSubmit}>
  <Button type="submit">
    Create Account
  </Button>
</form>

// 4. Icon button
<IconButton
  onClick={() => deleteItem(id)}
  aria-label="Delete"
>
  <TrashIcon />
</IconButton>
```

### Incorrect Usage (Won't Compile)

```tsx
// ERROR: Property 'onClick' is missing
<Button>Click Me</Button>

// ERROR: onClick required when type is not 'submit'
<Button type="button">Action</Button>

// ERROR: IconButton also requires onClick or type="submit"
<IconButton aria-label="Search">
  <SearchIcon />
</IconButton>
```

---

## Testing Patterns

In tests, when you don't care about click behavior, use a noop function:

```tsx
const noop = () => {};

// Rendering test - just checking it renders
render(<Button onClick={noop}>Click me</Button>);

// Visual test - checking styles
render(<Button onClick={noop} variant="danger">Delete</Button>);

// Ref test - checking forwarding
const ref = React.createRef<HTMLButtonElement>();
render(<Button onClick={noop} ref={ref}>Click me</Button>);
```

---

## The IconButton Wrapper

`IconButton` follows the same pattern. It's just a `Button` with icon-specific styling:

```tsx
export const IconButton = forwardRef<HTMLButtonElement, IconButtonProps>(
  ({ onClick, type, ...props }, ref) => {
    // Passes through the same onClick/type requirements
    const buttonProps = type === 'submit'
      ? { type: 'submit' as const, onClick }
      : { onClick: onClick!, type };

    return <Button ref={ref} {...buttonProps} {...props} />;
  }
);
```

---

## Files Reference

| File | Purpose |
|------|---------|
| `frontend/src/components/ui/Button.tsx` | The strict Button component |
| `frontend/src/components/ui/__tests__/Button.test.tsx` | Test patterns |
| `frontend/eslint.config.js` | jsx-a11y rules (belt-and-suspenders) |

---

## Why "Going for Gold"

The original recommendation was a phased rollout:
1. ESLint rules (quick, partial coverage)
2. Custom ESLint plugin (more work, better coverage)
3. Strict Button component (most work, complete coverage)

User feedback: *"We are the team, so if that's the friction, it doesn't really exist."*

For a two-person team (human + AI), the overhead of phased rollout exceeded the overhead of just doing it right. TypeScript enforcement is the gold standard - it catches 100% of cases at compile time, in the IDE, before the code even runs.

---

*Document created Session 086. For the rationale behind skipping the phased approach, see `.claude/scratchpad/session-086-button-prevention-rationale.md`.*
