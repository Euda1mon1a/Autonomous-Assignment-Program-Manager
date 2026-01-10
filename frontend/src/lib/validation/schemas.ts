/**
 * Validation schemas using Zod for frontend validation.
 *
 * Provides type-safe validation schemas for:
 * - Person data
 * - Assignment data
 * - Block data
 * - Swap requests
 * - Form inputs
 */

import { z } from "zod";

// ==================== Person Schemas ====================

export const personTypeSchema = z.enum(["resident", "faculty"]);

export const facultyRoleSchema = z.enum([
  "pd",
  "apd",
  "oic",
  "deptChief",
  "sportsMed",
  "core",
  "adjunct",
]);

export const pgyLevelSchema = z
  .number()
  .int()
  .min(1, "PGY level must be at least 1")
  .max(3, "PGY level must be at most 3");

export const personBaseSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters").max(255),
  type: personTypeSchema,
  email: z.string().email("Invalid email address").optional().nullable(),
  pgyLevel: pgyLevelSchema.optional().nullable(),
  performsProcedures: z.boolean().default(false),
  specialties: z.array(z.string()).optional().nullable(),
  primaryDuty: z.string().max(255).optional().nullable(),
  facultyRole: facultyRoleSchema.optional().nullable(),
});

export const personCreateSchema = personBaseSchema;

export const personUpdateSchema = personBaseSchema.partial();

export const personResponseSchema = personBaseSchema.extend({
  id: z.string().uuid(),
  createdAt: z.string().datetime(),
  updatedAt: z.string().datetime(),
  sundayCallCount: z.number().int().default(0),
  weekdayCallCount: z.number().int().default(0),
  fmitWeeksCount: z.number().int().default(0),
});

// ==================== Assignment Schemas ====================

export const assignmentRoleSchema = z.enum(["primary", "supervising", "backup"]);

export const assignmentBaseSchema = z.object({
  blockId: z.string().uuid(),
  personId: z.string().uuid(),
  rotationTemplateId: z.string().uuid().optional().nullable(),
  role: assignmentRoleSchema,
  activityOverride: z.string().max(255).optional().nullable(),
  notes: z.string().max(1000).optional().nullable(),
  overrideReason: z.string().max(500).optional().nullable(),
});

export const assignmentCreateSchema = assignmentBaseSchema.extend({
  createdBy: z.string().optional().nullable(),
});

export const assignmentUpdateSchema = assignmentBaseSchema
  .partial()
  .extend({
    updatedAt: z.string().datetime(),
    acknowledge_override: z.boolean().optional(),
  });

export const assignmentResponseSchema = assignmentBaseSchema.extend({
  id: z.string().uuid(),
  createdBy: z.string().optional().nullable(),
  createdAt: z.string().datetime(),
  updatedAt: z.string().datetime(),
  overrideAcknowledgedAt: z.string().datetime().optional().nullable(),
  confidence: z.number().min(0).max(1).optional().nullable(),
  score: z.number().optional().nullable(),
});

// ==================== Block Schemas ====================

export const blockSessionSchema = z.enum(["AM", "PM"]);

export const blockBaseSchema = z.object({
  date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, "Date must be in YYYY-MM-DD format"),
  session: blockSessionSchema,
});

export const blockResponseSchema = blockBaseSchema.extend({
  id: z.string().uuid(),
  createdAt: z.string().datetime(),
  updatedAt: z.string().datetime(),
});

// ==================== Swap Schemas ====================

export const swapTypeSchema = z.enum(["oneToOne", "absorb", "multi_way"]);

export const swapStatusSchema = z.enum([
  "pending",
  "approved",
  "executed",
  "rejected",
  "cancelled",
  "rolled_back",
]);

export const swapRequestSchema = z.object({
  requester_id: z.string().uuid(),
  requester_assignmentId: z.string().uuid(),
  target_id: z.string().uuid().optional().nullable(),
  target_assignmentId: z.string().uuid().optional().nullable(),
  swapType: swapTypeSchema,
  reason: z.string().min(10, "Reason must be at least 10 characters").max(500),
});

export const swapResponseSchema = swapRequestSchema.extend({
  id: z.string().uuid(),
  status: swapStatusSchema,
  createdAt: z.string().datetime(),
  approved_at: z.string().datetime().optional().nullable(),
  executedAt: z.string().datetime().optional().nullable(),
  approved_by: z.string().optional().nullable(),
});

// ==================== Filter Schemas ====================

export const dateRangeFilterSchema = z.object({
  startDate: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional(),
  endDate: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional(),
});

export const personFilterSchema = z.object({
  person_type: personTypeSchema.optional(),
  pgyLevel: pgyLevelSchema.optional(),
  facultyRole: facultyRoleSchema.optional(),
  specialties: z.array(z.string()).optional(),
  performsProcedures: z.boolean().optional(),
});

export const assignmentFilterSchema = z.object({
  personId: z.string().uuid().optional(),
  blockId: z.string().uuid().optional(),
  rotationTemplateId: z.string().uuid().optional(),
  role: assignmentRoleSchema.optional(),
  dateRange: dateRangeFilterSchema.optional(),
});

// ==================== Pagination Schemas ====================

export const paginationParamsSchema = z.object({
  page: z.number().int().min(1).default(1),
  pageSize: z.number().int().min(1).max(1000).default(50),
});

export const sortOrderSchema = z.enum(["asc", "desc"]);

export const sortParamsSchema = z.object({
  sort_by: z.string(),
  sort_order: sortOrderSchema.default("asc"),
});

// ==================== Form Validation Schemas ====================

export const emailSchema = z
  .string()
  .email("Invalid email address")
  .min(1, "Email is required");

export const phoneSchema = z
  .string()
  .regex(/^[\d\s\-\(\)\+\.]+$/, "Invalid phone number format")
  .optional()
  .or(z.literal(""));

export const passwordSchema = z
  .string()
  .min(12, "Password must be at least 12 characters")
  .regex(/[A-Z]/, "Password must contain at least one uppercase letter")
  .regex(/[a-z]/, "Password must contain at least one lowercase letter")
  .regex(/\d/, "Password must contain at least one digit")
  .regex(/[!@#$%^&*(),.?":{}|<>]/, "Password must contain at least one special character");

export const dateStringSchema = z
  .string()
  .regex(/^\d{4}-\d{2}-\d{2}$/, "Date must be in YYYY-MM-DD format");

// ==================== Type Exports ====================

export type PersonType = z.infer<typeof personTypeSchema>;
export type FacultyRole = z.infer<typeof facultyRoleSchema>;
export type PersonBase = z.infer<typeof personBaseSchema>;
export type PersonCreate = z.infer<typeof personCreateSchema>;
export type PersonUpdate = z.infer<typeof personUpdateSchema>;
export type PersonResponse = z.infer<typeof personResponseSchema>;

export type AssignmentRole = z.infer<typeof assignmentRoleSchema>;
export type AssignmentBase = z.infer<typeof assignmentBaseSchema>;
export type AssignmentCreate = z.infer<typeof assignmentCreateSchema>;
export type AssignmentUpdate = z.infer<typeof assignmentUpdateSchema>;
export type AssignmentResponse = z.infer<typeof assignmentResponseSchema>;

export type BlockSession = z.infer<typeof blockSessionSchema>;
export type BlockBase = z.infer<typeof blockBaseSchema>;
export type BlockResponse = z.infer<typeof blockResponseSchema>;

export type SwapType = z.infer<typeof swapTypeSchema>;
export type SwapStatus = z.infer<typeof swapStatusSchema>;
export type SwapRequest = z.infer<typeof swapRequestSchema>;
export type SwapResponse = z.infer<typeof swapResponseSchema>;

export type DateRangeFilter = z.infer<typeof dateRangeFilterSchema>;
export type PersonFilter = z.infer<typeof personFilterSchema>;
export type AssignmentFilter = z.infer<typeof assignmentFilterSchema>;

export type PaginationParams = z.infer<typeof paginationParamsSchema>;
export type SortOrder = z.infer<typeof sortOrderSchema>;
export type SortParams = z.infer<typeof sortParamsSchema>;
