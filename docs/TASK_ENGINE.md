# Task Engine

## Model

```
Task
  task_id
  parent_task_id | null
  title
  description
  assigned_agent | unassigned | all
  status: draft | queued | processing | blocked | review | accepted | rejected | done
  dependencies[]
  result | null
  created_at
  updated_at
```

## Loop

analyze -> propose -> delegate -> answer -> critique -> improve -> review -> accept|reject -> summary -> learn

## Human controls

create, assign, pause, resume, approve, reject.

## Storage

Phase 1: `data/tasks.json`
