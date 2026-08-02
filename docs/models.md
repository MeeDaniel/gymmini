# Data Models in Gymmini

## Database Schema Structure

The database is built on SQLAlchemy 2.0 with asynchronous drivers (aiosqlite). It models the relationship between users, workout templates, exercises, and their actual execution (notes and sets).

### 1. User
`users` table:
- `id` (int, PK)
- `telegram_id` (int, nullable, unique): Nullable to support future web-only users.
- `telegram_alias` (str, nullable)

### 2. Exercise
`exercises` table:
- `id` (int, PK)
- `user_id` (int, FK)
- `name` (str)
- `type` (Enum: `ExerciseType`):
  - `strength`: Reps + Weight
  - `cardio`: Distance + Duration
  - `bodyweight`: Reps only
  - `timed`: Duration only
- `description` (str, nullable)
- `image_path` (str, nullable)

### 3. Workout (Template)
`workouts` table:
- `id` (int, PK)
- `user_id` (int, FK)
- `brief` (str)
- `description` (str, nullable)

**Association Table**: `workout_exercises`
Links templates and exercises.
- `workout_id` (int, FK)
- `exercise_id` (int, FK)
- `sort_order` (int): Determines the specific order of the exercise within the template.

### 4. WorkoutNote
`workout_notes` table:
The actual instantiated workout session.
- `id` (int, PK)
- `user_id` (int, FK)
- `workout_id` (int, FK, nullable): Link to the original template, if any.
- `brief` (str)
- `description` (str, nullable)
- `started_at` (datetime): Exact date and time the workout started.

### 5. ExerciseNote
`exercise_notes` table:
The instantiated exercise during a workout session.
- `id` (int, PK)
- `exercise_id` (int, FK)
- `workout_note_id` (int, FK)
- `sort_order` (int): Preserves the order from the template, or the order they were added.
- `notes` (str, nullable)

### 6. Set
`sets` table:
The individual sets performed for an ExerciseNote.
- `id` (int, PK)
- `exercise_note_id` (int, FK)
- `sort_order` (int): Order in which the sets were performed.
- `reps` (int, nullable)
- `weight` (float, nullable)
- `duration` (float, nullable)
- `distance` (float, nullable)
