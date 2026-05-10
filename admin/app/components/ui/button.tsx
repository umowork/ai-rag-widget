"use client";

import { ButtonHTMLAttributes, forwardRef } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "outline" | "ghost" | "destructive" | "success";
  size?: "sm" | "md" | "lg";
}

const variantStyles: Record<string, string> = {
  default: "bg-blue-600 text-white hover:bg-blue-500",
  outline: "border border-slate-600 text-slate-200 hover:bg-slate-700",
  ghost: "text-slate-300 hover:bg-slate-700 hover:text-slate-100",
  destructive: "bg-red-600 text-white hover:bg-red-500",
  success: "bg-emerald-600 text-white hover:bg-emerald-500",
};

const sizeStyles: Record<string, string> = {
  sm: "px-3 py-1.5 text-sm",
  md: "px-4 py-2 text-sm",
  lg: "px-6 py-3 text-base",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "default", size = "md", className = "", disabled, children, ...props }, ref) => {
    const base =
      "inline-flex items-center justify-center rounded-lg font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-slate-900 disabled:opacity-50 disabled:pointer-events-none";
    return (
      <button
        ref={ref}
        className={`${base} ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
        disabled={disabled}
        {...props}
      >
        {children}
      </button>
    );
  }
);
Button.displayName = "Button";
