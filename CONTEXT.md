# Adaptive Control

Adaptive Control models independent, typed controllers that adapt a Home
Assistant environment from explicit signals without replacing Home Assistant's
general automation engine.

## Language

**Controller**:
An independently configured unit that evaluates signals and commands its owned actuators.
_Avoid_: Automation, rule, space

**Controller Type**:
A reusable kind of adaptive behavior with defined signal roles, actuator roles, and policy settings.
_Avoid_: Plugin, template, automation type

**Signal**:
A named observation consumed by one or more controllers when making decisions.
_Avoid_: Trigger, condition

**Signal Provider**:
An independently configured unit that derives and publishes reusable signals without commanding actuators.
_Avoid_: Controller, hidden helper

**Context Input**:
A stateful Home Assistant entity binding that represents a continuing condition relevant to a controller.
_Avoid_: Event, command

**Input Role**:
A controller-type-defined semantic input slot with requiredness and value-quality expectations.
_Avoid_: Entity selector, raw entity ID

**Binding**:
An explicit user-confirmed association between a controller role and a Home Assistant entity.
_Avoid_: Area membership, automatic discovery

**Aggregation Policy**:
A controller-type-defined method for deriving one input-role value from multiple bound signals.
_Avoid_: Arbitrary template, user formula

**Signal Quality**:
The controller-visible validity of an input value, including valid, unavailable, invalid, and explicitly age-limited stale states.
_Avoid_: Device health, source priority

**Command Input**:
A one-time instruction delivered to a controller without representing a continuing condition.
_Avoid_: Context, persistent state

**Profile**:
A controller-specific desired configuration selected from its current signals, context inputs, and policy.
_Avoid_: Context, Home Assistant scene

**System Profile**:
A controller-type-defined profile that represents an intrinsic algorithm state and cannot be added or removed by a user.
_Avoid_: User preset, editable scene

**Custom Profile**:
A user-defined profile permitted by a controller type and constrained by that type's profile schema.
_Avoid_: Arbitrary automation, controller type

**Stateful Output**:
An actuator state that a controller maintains while its effective profile remains active.
_Avoid_: Transition command, one-time action

**Transition Action**:
A one-time command issued when a profile becomes effective and not continuously reconciled afterward.
_Avoid_: Stateful output, profile

**Profile Request**:
An external request for a named profile with an identified source, authority, and lifetime.
_Avoid_: Context input, direct actuator command

**Safety Constraint**:
A non-overridable controller-type restriction that limits which actuator states are permitted.
_Avoid_: High-priority profile, override

**Fallback Policy**:
Controller-type-specific behavior used when an input role cannot provide a valid signal.
_Avoid_: Global fail-safe, default profile

**Actuator**:
A Home Assistant entity that a controller may command.
_Avoid_: Target, output device

**Ownership**:
The exclusive authority of one controller to issue automatic commands to an actuator.
_Avoid_: Binding, lock

**External Change**:
An actuator change not issued by its owning controller, including physical, user, and other-automation changes.
_Avoid_: Conflict, manual change

**Intervention Policy**:
Controller-type-specific rules that interpret an external change and decide whether to accept it, resist it, or temporarily yield to it.
_Avoid_: Global override behavior, conflict policy

**Override**:
A temporary controller state that preserves external intent until a controller-type-specific reset condition is met.
_Avoid_: Disabled, ownership transfer

**Area**:
A Home Assistant organizational assignment used for placement and configuration suggestions, not as a shared runtime controller.
_Avoid_: Space, controller group

## Relationships

- A **Controller** has exactly one **Controller Type**
- A **Controller Type** is implemented and versioned by the integration rather than defined as an arbitrary user rule graph
- A **Controller** consumes one or more **Signals**
- Multiple **Controllers** may consume the same **Signal**
- A **Signal Provider** consumes one or more **Signals** and publishes one or more derived **Signals**
- A **Signal Provider** has no **Actuators**, **Profiles**, **Overrides**, or **Profile Requests**
- A **Controller** may bind either a source entity or a **Signal Provider** output to an **Input Role**
- A **Controller Type** declares its supported **Context Inputs** and **Command Inputs**
- A **Controller Type** declares each **Input Role** as required or optional and defines its accepted **Signal Quality**
- A **Controller Type** defines a **Fallback Policy** for every required **Input Role**
- Every **Input Role** and **Actuator** association is an explicit **Binding**
- An **Input Role** may accept one or more **Bindings** only when its **Controller Type** permits it
- A multi-binding **Input Role** uses an **Aggregation Policy** offered by its **Controller Type**
- An **Aggregation Policy** accounts for the **Signal Quality** of every bound signal
- An **Area** may suggest entities but does not create or change a **Binding**
- A newly discovered Home Assistant entity does not affect a **Controller** until a user confirms a new **Binding**
- Multiple **Controllers** may bind the same Home Assistant state to a **Context Input**
- A continuing condition is represented by a **Context Input**, not a **Command Input**
- A **Controller** selects at most one effective **Profile** at a time
- A **Controller Type** determines whether it supports **System Profiles**, **Custom Profiles**, or both
- A **System Profile** and **Custom Profile** share the same priority and effective-profile semantics
- A **Profile** contains zero or more **Stateful Outputs** and zero or more **Transition Actions**
- A **Controller** reconciles a **Stateful Output** while its **Profile** remains effective
- A **Transition Action** runs only when its **Profile** becomes effective
- A **Profile Request** has normal or forced authority and remains active until expiry or explicit release
- A **Safety Constraint** takes precedence over every **Profile Request**, **Override**, and automatic **Profile**
- A forced **Profile Request** takes precedence over an **Override**
- An **Override** takes precedence over a normal **Profile Request**
- A normal **Profile Request** takes precedence over an automatically selected **Profile**
- When a **Profile Request** or **Override** ends, the **Controller** selects a new **Profile** from current inputs rather than restoring an earlier actuator state
- A **Controller** owns one or more **Actuators**
- An **Actuator** is owned by at most one **Controller**
- An **External Change** does not transfer **Ownership**
- A **Controller Type** defines its **Intervention Policy**
- An **External Change** may start an **Override** according to the owning controller's **Intervention Policy**
- An **Override** does not suspend safety constraints or transfer **Ownership**
- Recovery of a valid **Signal** causes a fresh **Profile** selection rather than replay of commands accumulated during fallback
- An **Area** may organize any number of independent **Controllers**

## Example dialogue

> **Dev:** "Can Adaptive Lighting and Mirror Defogging both use the bathroom humidity reading?"
> **Domain expert:** "Yes. They are independent Controllers consuming the same Signal, but each owns different Actuators."

> **Dev:** "Does manually turning on the mirror heater disable its safety limit?"
> **Domain expert:** "No. The External Change may start an Override, but the Controller retains Ownership and continues enforcing its safety constraints."

## Flagged ambiguities

- "space" previously meant both a Home Assistant room and one area-wide runtime coordinator; resolved: use **Area** only for organization and independent **Controllers** for runtime behavior.
- "automation" could mean either a Home Assistant automation or adaptive behavior; resolved: use **Controller** for a configured adaptive unit and **Controller Type** for its reusable behavior.
- "extensible" could mean either adding tested controller modules or allowing arbitrary user code and rules; resolved: extend the integration with versioned **Controller Types**.
- "target" could mean an entity selected by a condition or an entity being commanded; resolved: use **Actuator** only for the commanded entity.
- "scene" was used for both an active semantic condition and a Home Assistant action snapshot; resolved: use **Context Input** for the condition and **Profile** for a controller's desired configuration.
- "input" was used for both continuing state and a one-time instruction; resolved: use **Context Input** and **Command Input** respectively.
- "profile action" could mean either maintained state or a one-time command; resolved: use **Stateful Output** and **Transition Action** respectively.
- "shared calculation" could mean duplicated controller logic or a hidden shared runtime object; resolved: publish it through an independent **Signal Provider**.
