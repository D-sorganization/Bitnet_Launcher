## 2023-10-27 - PyQt6 Standalone Input Accessibility

**Learning:** In PyQt6, `QLineEdit` and `QTextEdit` widgets that do not have a corresponding `QLabel` associated via `setBuddy()` are silent or generic to screen readers.
**Action:** Always use `setAccessibleName()` on standalone input fields and read-only text areas (like search bars or chat displays) to ensure screen readers can announce their purpose correctly.

## 2025-01-28 - Dynamic Tooltips for Disabled Buttons

**Learning:** In PyQt6, disabling a button (`setEnabled(False)`) makes it unresponsive, but a tooltip can still be displayed if hovered, which is crucial for explaining _why_ an action is unavailable (e.g., "Model already installed" or "Download in progress").
**Action:** When conditionally disabling a button, always update its `setToolTip()` string to provide context instead of leaving the user guessing.

## 2024-05-24 - Qt Stylesheet Focus Indicators

**Learning:** The app uses a custom Qt stylesheet (Catppuccin) which overrides default OS focus indicators for keyboard navigation, hiding tab focus.
**Action:** Always explicitly add `:focus` pseudo-class rules (e.g. `border: 1px solid {t.ACCENT};`) to interactive UI components when writing or modifying Qt stylesheets to preserve keyboard accessibility.

## 2024-04-26 - Disabled Button Tooltips

**Learning:** When conditionally disabling a button (`setEnabled(False)`), screen reader users or keyboard navigators may still focus on or interact with the space, and the tooltip is still visible on disabled elements. It helps users to know _why_ the button is unavailable.
**Action:** Always update the `setToolTip()` string of a button when disabling it to explain the state (e.g., "An operation is currently in progress"), and restore the original tooltip when re-enabling it.

## 2024-05-25 - QLabel Rich Text Auto-detection

**Learning:** By default, `QLabel` in PyQt6 uses `Qt.TextFormat.AutoText`, which parses HTML. If untrusted dynamic text (like file paths or names) is set, any text resembling HTML tags (like `<` or `>`) will be incorrectly parsed and rendered, potentially hiding information or leading to Rich Text injection.
**Action:** Always apply `.setTextFormat(Qt.TextFormat.PlainText)` on `QLabel` instances that display untrusted or dynamic text where HTML is not intended.

## 2024-05-18 - QLineEdit Clear Button

**Learning:** PyQt6's `QLineEdit` has a built-in `setClearButtonEnabled(True)` method that adds a handy 'x' button inside the text field when it has content. This provides a standard and accessible way for users to quickly clear input without manually selecting and deleting it.
**Action:** When creating text input fields (`QLineEdit`) where users might want to easily clear their entire input (like chat messages, search fields, or path inputs), explicitly enable this feature for better UX.

## 2024-05-01 - Dynamic Tooltips for Disabled States

**Learning:** Setting static tooltips on disabled elements is helpful, but updating the tooltip text dynamically based on the state (e.g. why the button is disabled) creates a much more intuitive and user-friendly experience, as it gives users actionable feedback on how to enable the action.
**Action:** When conditionally disabling an action button (`setEnabled(False)`), immediately update its `setToolTip()` string to explain the specific reason the action is currently unavailable.

## 2026-05-03 - Unified Dialog Stylesheet Focus Indicators

**Learning:** In a codebase with custom stylesheets, using a centrally defined stylesheet (like `get_hub_dialog_stylesheet()`) across similar dialogs ensures consistent accessibility features like `:focus` indicators are applied everywhere, rather than relying on duplicated local definitions that might be missing them.
**Action:** When adding or improving styles, look for opportunities to replace locally-defined stylesheets lacking accessibility with centralized, complete ones to ensure consistent behavior across the application.

## 2026-06-22 - PyQt Inline Stylesheets Disable Global Focus Styles

**Learning:** Using an inline `.setStyleSheet()` on a Qt widget overrides the application-level global stylesheet for that widget. If the inline stylesheet does not explicitly define a `:focus` pseudo-class rule, keyboard users will lose all visual indication when the widget receives focus.
**Action:** When applying an inline stylesheet to an interactive or focusable widget (like `QTextEdit` or `QLineEdit`), always include a corresponding `:focus` rule (e.g., `border: 1px solid {accent_color};`) to preserve keyboard accessibility.

## 2025-05-07 - Rich Empty States in QListWidget

**Learning:** Adding a simple text item to an empty `QListWidget` looks like a selectable interactive element, which can confuse users.
**Action:** When displaying an empty state in a list, add a `QListWidgetItem` but explicitly disable its selection and interaction flags (`setFlags(Qt.ItemFlag.NoItemFlags)`), center the text, and use a subdued color (`t.SUBTEXT`) to clearly communicate it is an empty state message and not data.

## 2025-02-13 - Stateful Tooltips Cleanup

**Learning:** When conditionally disabling a button (`setEnabled(False)`) and updating its `setToolTip()` string to explain why it is unavailable, if the button is subsequently re-enabled, the tooltip persists unless explicitly cleared.
**Action:** Explicitly clear (`setToolTip("")`) or reset the tooltip when re-enabling a conditionally disabled button to prevent stale state messages from persisting.

## 2025-05-14 - Empty States in QTableWidget

**Learning:** When displaying an empty state message in a `QTableWidget` by inserting a row, the message often gets cut off by columns, and users might try to select the row thinking it's interactive data.
**Action:** When adding an empty state to a table, use `clearSpans()` and `setSpan(0, 0, 1, column_count)` to make the message span the entire width of the table. Center the text, apply a subdued color, and use `setFlags(Qt.ItemFlag.NoItemFlags)` to prevent the row from being selected or interacted with.

## 2025-02-12 - Empty State for Chat Window

**Learning:** Adding `setPlaceholderText` to a `QTextEdit` that is set as read-only (`setReadOnly(True)`) provides an excellent, native way to display an empty state or call-to-action without needing complex overlay widgets or toggling text visibility when an interaction begins.
**Action:** Use `setPlaceholderText()` on main `QTextEdit` and `QLineEdit` components to guide users when no content is present, especially when waiting for an initial interaction.

## 2024-05-18 - Proactive Button Disabling Over Error Dialogs

**Learning:** In PyQt applications, relying on a `QMessageBox` to tell users "Please select an item first" after they click an action button is poor UX. `LauncherWindow` used this anti-pattern while `HubDialog` proactively disabled buttons.
**Action:** When an action button requires a selection from a list or table to function, proactively disable it (`setEnabled(False)`) when the selection is empty and provide a clear tooltip explaining why, rather than allowing the click and showing an error popup.

## 2025-05-17 - Proactive Button Disabling for Prerequisites

**Learning:** Relying on `QMessageBox` popups to inform a user that a prerequisite is missing (e.g., "BitNet not installed" when clicking Download, or "BitNet root does not exist" when clicking Build) is an interruptive anti-pattern. Users shouldn't be able to click an action that is guaranteed to fail due to a known state.
**Action:** Extend the proactive disabling pattern (`setEnabled(False)`) to cover not just missing selections (like "No model selected") but also missing prerequisite states (like "App not installed"). Always update the `setToolTip()` to explain exactly what prerequisite must be met to enable the button.

## 2024-05-24 - PyQt Inline Stylesheets Disable Global Focus Styles

**Learning:** Using an inline `.setStyleSheet()` on a Qt widget overrides the application-level global stylesheet for that widget. If the inline stylesheet does not explicitly define a `:focus` pseudo-class rule, keyboard users will lose all visual indication when the widget receives focus.
**Action:** When applying an inline stylesheet to an interactive or focusable widget (like `QPushButton`, `QTextEdit`, or `QLineEdit`), always include a corresponding `:focus` rule (e.g., `border: 1px solid {accent_color}; outline: none;`) to preserve keyboard accessibility.

## 2024-05-19 - QSpinBox unit context

**Learning:** Adding a suffix to numeric inputs, like QSpinBox, provides immediate, inline context (e.g. " threads"), clarifying the unit of measurement right within the input field.
**Action:** Use `.setSuffix(" <unit>")` on numerical inputs where the unit is relevant, such as QSpinBox and QDoubleSpinBox, for improved UX readability.

## 2026-05-20 - Decorative Unicode Characters in Buttons

**Learning:** When using decorative Unicode characters (like ▶ or ⚙) in `QPushButton` text to simulate icons without external image dependencies, screen readers announce the literal character names (e.g., "Black right-pointing triangle"), which clutters the UI and confuses users.
**Action:** Always set `setAccessibleName()` on buttons with decorative Unicode text to provide a clean, text-only label for screen reader users.

## 2026-05-29 - Native Alt+Letter Shortcuts for QPushButtons

**Learning:** Adding an ampersand (`&`) to `QPushButton` text automatically provides a native Alt+Letter keyboard shortcut (e.g., Alt+C for "Chat &Here") and renders a visual underline on the shortcut letter in PyQt applications. This significantly improves keyboard accessibility and power-user navigation without requiring custom key event handling.
**Action:** Always evaluate main action buttons for native shortcut opportunities and add ampersands to their text, taking care to avoid conflicting shortcut letters within the same window context.

## 2025-05-18 - QTableWidget Selection Constraints

**Learning:** In PyQt6, `QTableWidget` allows multi-selection by default (e.g. holding Shift/Ctrl), even when `SelectionBehavior` is set to `SelectRows`. If the intended UX only supports a single action at a time (like downloading one model, or previewing one item's details in a label), allowing multi-selection causes a confusing disconnect between the highlighted state and the actual executed action.
**Action:** When a table's primary action only applies to one item, explicitly enforce single selection by adding `.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)`.
## 2026-06-12 - Disable Native Focus Ring in Custom Stylesheets

**Learning:** When applying an inline custom stylesheet to an interactive or focusable widget (like `QTextEdit`), defining a `:focus` pseudo-class with a custom border is necessary for keyboard accessibility. However, without explicitly removing the native outline, some OS environments will render a dotted native focus ring overlapping the custom border, causing visual clutter.
**Action:** Always append `outline: none;` to the `:focus` selector rule (e.g., `border: 1px solid {t.ACCENT}; outline: none;`) in Qt stylesheets to ensure only the custom focus indicator is shown.

## 2026-06-22 - Jargon Tooltips for Form Fields

**Learning:** When form fields use domain-specific jargon or technical hyperparameters (like "System Prompt", "Temperature", or "Context size"), non-technical users may not understand what they do.
**Action:** Always add descriptive tooltips (`setToolTip()`) to both the input widget and its associated label to explain the purpose of complex settings in plain language, making the UI more intuitive for all users.

## 2024-06-21 - Added Tooltips to Dynamically Generated Labels
**Learning:** In PyQt6 layout helper functions that dynamically generate a `QLabel` for an input widget, the label often lacks the necessary jargon explanations that the input widget itself provides via tooltips.
**Action:** Always programmatically copy the input's tooltip to the label (e.g., `if widget.toolTip(): lbl.setToolTip(widget.toolTip())`) so both elements display necessary jargon explanations on hover.
