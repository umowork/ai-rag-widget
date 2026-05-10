import { HTMLAttributes, forwardRef } from "react";

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "success" | "warning" | "destructive" | "outline";
}

const variantStyles: Record<string, string> = {
  default: "bg-slate-600 text-slate-100",
  success: "bg-emerald-600/20 text-emerald-400 border border-emerald-600/40",
  warning: "bg-amber-600/20 text-amber-400 border border-amber-600/40",
  destructive: "bg-red-600/20 text-red-400 border border-red-600/40",
  outline: "border border-slate-600 text-slate-300",
};

export const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
  ({ variant = "default", className = "", children, ...props }, ref) => (
    <span
      ref={ref}
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${variantStyles[variant]} ${className}`}
      {...props}
    >
      {children}
    </span>
  )
);
Badge.displayName = "Badge";
