# SAFA Invoice System: Process Workflows

## Invoice Lifecycle Diagram

```
┌───────────────────┐     ┌───────────────────┐     ┌───────────────────┐
│                   │     │                   │     │                   │
│  Invoice Creation ├────►│ Payment Processing├────►│  Status Update    │
│                   │     │                   │     │                   │
└───────┬───────────┘     └─────────┬─────────┘     └─────────┬─────────┘
        │                           │                         │
        ▼                           ▼                         ▼
┌───────────────────┐     ┌───────────────────┐     ┌───────────────────┐
│                   │     │                   │     │                   │
│ Auto: Registration│     │ EFT/Bank Transfer │     │  Update to PAID   │
│ Manual: Admin     │     │ Card Payment      │     │  Player Activation│
│                   │     │                   │     │                   │
└───────────────────┘     └───────────────────┘     └───────────────────┘
```

## Registration and Invoice Flow

```
┌─────────────┐     ┌──────────────┐     ┌────────────────┐     ┌─────────────┐
│             │     │              │     │                │     │             │
│ Start       ├────►│ Enter Player ├────►│ Review Payment ├────►│ Complete    │
│ Registration│     │ Details      │     │ Information    │     │ Registration│
│             │     │              │     │                │     │             │
└─────────────┘     └──────────────┘     └────────────────┘     └──────┬──────┘
                                                                       │
                                                                       ▼
┌─────────────┐     ┌──────────────┐     ┌────────────────┐     ┌─────────────┐
│             │     │              │     │                │     │             │
│ Player      │◄────┤ Player Status│◄────┤ Payment        │◄────┤ Invoice     │
│ Activated   │     │ Updated      │     │ Confirmation   │     │ Generated   │
│             │     │              │     │                │     │             │
└─────────────┘     └──────────────┘     └────────────────┘     └─────────────┘
```

## Payment Processing Workflow

```
┌──────────────┐
│              │
│ New Invoice  ├─────┐
│ (PENDING)    │     │
│              │     │
└──────────────┘     │
                     │
                     ▼
        ┌─────────────────────┐
        │                     │
        │  Payment Method?    │
        │                     │
        └─┬───────────────────┘
          │
    ┌─────┴──────┐
    │            │
    ▼            ▼
┌────────┐  ┌─────────┐
│        │  │         │
│  EFT   │  │  Card   │
│        │  │         │
└───┬────┘  └────┬────┘
    │           │
    ▼           ▼
┌────────┐  ┌─────────┐
│Manual  │  │Automatic│
│Admin   │  │Gateway  │
│Verify  │  │Process  │
└───┬────┘  └────┬────┘
    │           │
    └─────┬─────┘
          │
          ▼
┌──────────────┐     ┌──────────────┐     ┌────────────┐
│              │     │              │     │            │
│ Update       ├────►│ Set Payment  ├────►│ Activate   │
│ Status: PAID │     │ Date         │     │ Player     │
│              │     │              │     │            │
└──────────────┘     └──────────────┘     └────────────┘
```

## Overdue Management Process

```
┌──────────────┐     ┌──────────────┐     ┌────────────────┐
│              │     │              │     │                │
│ Daily Check  ├────►│ Identify     ├────►│ Update Status  │
│ (Scheduled)  │     │ Due Invoices │     │ to OVERDUE     │
│              │     │              │     │                │
└──────────────┘     └──────────────┘     └───────┬────────┘
                                                  │
                                                  ▼
┌──────────────┐     ┌──────────────┐     ┌────────────────┐
│              │     │              │     │                │
│ Follow-up    │◄────┤ Send Email   │◄────┤ Generate       │
│ Actions      │     │ Notifications│     │ Overdue Report │
│              │     │              │     │                │
└──────────────┘     └──────────────┘     └────────────────┘
```

## Reporting Hierarchy

```
┌───────────────────────────────────────────────────────────┐
│                      All Invoices                         │
└───────┬───────────────────────────────────────┬───────────┘
        │                                       │
        ▼                                       ▼
┌───────────────┐                      ┌───────────────┐
│  By Status    │                      │  By Entity    │
└───┬───┬───┬───┘                      └───┬───┬───┬───┘
    │   │   │                              │   │   │
    ▼   ▼   ▼                              ▼   ▼   ▼
┌─────┐ ┌─────┐ ┌─────┐              ┌─────┐ ┌─────┐ ┌─────┐
│Paid │ │Pend-│ │Over-│              │Club │ │ LFA │ │Reg- │
│     │ │ing  │ │due  │              │     │ │     │ │ion  │
└─────┘ └─────┘ └─────┘              └─────┘ └─────┘ └─────┘
```

## Permission Structure

```
┌───────────────────────────┐
│   System Administrator    │
│                           │
│  - Full Access            │
└───────────┬───────────────┘
            │
            ▼
┌───────────────────────────┐
│     Provincial Admin      │
│                           │
│  - Province-wide Access   │
└───────────┬───────────────┘
            │
            ▼
┌───────────────────────────┐
│      Regional Admin       │
│                           │
│  - Region-wide Access     │
└───────────┬───────────────┘
            │
            ▼
┌───────────────────────────┐
│        LFA Admin          │
│                           │
│  - LFA-wide Access        │
└───────────┬───────────────┘
            │
            ▼
┌───────────────────────────┐
│     Club Administrator    │
│                           │
│  - Club-wide Access       │
└───────────┬───────────────┘
            │
            ▼
┌───────────────────────────┐
│         Player            │
│                           │
│  - Personal Access Only   │
└───────────────────────────┘
```

## Data Model Relationships

```
┌──────────────┐     ┌──────────────┐
│              │     │              │
│    Player    │◄────┤   Invoice    │
│              │     │              │
└──────┬───────┘     └──────┬───────┘
       │                    │
       │                    │
       │                    ▼
       │             ┌──────────────┐
       │             │              │
       └────────────►│ Registration │
                     │              │
                     └──────────────┘
                            ▲
                            │
                            │
                     ┌──────────────┐
                     │              │
                     │     Club     │
                     │              │
                     └──────┬───────┘
                            │
                            │
                            ▼
                     ┌──────────────┐
                     │              │
                     │     LFA      │
                     │              │
                     └──────────────┘
```

---

*These diagrams provide a visual representation of the SAFA Global invoice system workflows and relationships.*
