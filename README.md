# Booking-System with restful api
# Serializer Overview

This Django project includes a set of serializers to manage user authentication, appointments, lessons, and more. Below is a brief overview of each serializer and its role:

## CustomUserCreateSerializer

Manages user creation with fields for email, name, password, and user roles (teacher, student, center). Includes email validation and password generation.

- **Fields**: `id`, `email`, `name`, `password`, `is_teacher`, `is_student`, `is_center`, `is_active`, `is_staff`
- **Methods**:
  - `validate_email`: Ensures an email is provided.
  - `create`: Handles user creation, setting a password if not provided, and using a helper method `generate_password` to create a random one.
  - `generate_password`: Generates a random password.

## CustomTokenObtainPairSerializer

Customizes JWT token responses to include user roles and active status.

- **Methods**:
  - `get_token`: Adds custom claims (`is_active`, `is_teacher`, `is_student`, `is_center`) to the token.
  - `validate`: Adds user type information to the response data.

## CenterSerializer

Handles serialization for the `Center` model, including fields for user and address.

- **Fields**: `id`, `user`, `address`

## StudentSerializer

Manages student creation and updates, linking students with user data and centers. Includes functionality to generate a random password and send a welcome email.

- **Fields**: `id`, `user`, `lastname`, `phone`, `center`, `created_at`, `delete_confirmed`
- **Methods**:
  - `create`: Creates a `Student` instance and associated user, generating a random password and sending a welcome email.
  - `update`: Updates a `Student` instance and associated user data.

## DateSlotSerializer

Handles date slots, including fields for availability and time. Customizes output to include availability status.

- **Fields**: All fields from the `DateSlot` model.
- **Methods**:
  - `get_status`: Returns the availability status as a string ("true" or "false").
  - `create`: Handles creation, ensuring the 'teacher' field is managed correctly.
  - `update`: Handles updates, ensuring the 'status' field is managed correctly.
  - `to_representation`: Customizes the output to include the 'status' field.

## CourseSerializer

Manages courses with fields for title, description, and creation date.

- **Fields**: `id`, `title`, `description`, `created_at`

## TeacherSerializer

Handles teacher creation and updates, linking teachers with user data, centers, courses, and time slots.

- **Fields**: `id`, `user`, `lastname`, `phone`, `center`, `center_id`, `time_slots`, `courses`, `created_at`
- **Methods**:
  - `create`: Creates a `Teacher` instance and associated user, and links courses.
  - `update`: Updates a `Teacher` instance and associated user data, and manages courses.

## LessonSerializer

Manages lessons, linking them with date slots, teachers, and subjects. Includes fields for the number of students and duration.

- **Fields**: `id`, `day`, `max_students`, `times`, `teacher`, `subject`, `created_at`, `duration_days`
- **Methods**:
  - `create`: Creates a `Lesson` instance and links related data.
  - `update`: Updates a `Lesson` instance and manages related data.

## AppointmentSerializer

Handles appointments, linking them with users, centers, subjects, and time slots. Ensures date slot availability and marks slots as unavailable after booking.

- **Fields**: `id`, `user`, `center`, `subject`, `lesson`, `time_slot`, `duration`
- **Methods**:
  - `create`: Creates an `Appointment` instance, ensuring the `DateSlot` is available and marking it as unavailable after creation.
  - `to_representation`: Customizes the output to include detailed user, center, and time slot information.
  - `save`: Ensures a `DateSlot` is created if it doesn't exist when saving an appointment.

## SubjectSerializer

Manages courses with related teachers.

- **Fields**: All fields from the `Course` model.

## BookingSerializer

Handles bookings, linking them with students and date slots. Includes related objects in the output.

- **Fields**: `id`, `student`, `date_slot`
- **Meta Option**: `depth = 2` to include related objects in the output.

## EnrollmentSerializer

Manages enrollments, ensuring students are not enrolled in the same course multiple times. Links enrollments with students and courses.

- **Fields**: `id`, `student`, `course`, `enrolled_at`
- **Methods**:
  - `validate`: Ensures a student is not already enrolled in a course.
  - `create`: Associates the student from the request context with the enrollment.

These serializers use Django REST Framework features and integrate with third-party packages like `djoser` and `rest_framework_simplejwt` to provide robust API functionality for user management and scheduling within the application.

