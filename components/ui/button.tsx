import React from "react";

interface ButtonProps {
  className?: string;
  children: React.ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  variant?: "default" | "secondary" | "outline" | "ghost";
  type?: "button" | "submit" | "reset";
  size?: "default" | "sm" | "lg";
}

export function Button({
  className = "",
  children,
  onClick,
  disabled = false,
  variant = "default",
  type = "button",
  size = "default",
}: ButtonProps) {
  const variantClasses = {
    default: "bg-primary text-primary-foreground hover:bg-primary/90",
    secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/90",
    outline: "border border-input hover:bg-accent hover:text-accent-foreground",
    ghost: "hover:bg-accent hover:text-accent-foreground",
  };
  const sizeClasses = {
    default: "h-10 px-4 py-2 text-sm",
    sm: "h-9 px-3 text-xs",
    lg: "h-11 px-8 text-base",
  };

  return (
    <button
      type={type}
      className={`inline-flex items-center justify-center rounded-md font-medium transition-colors 
      focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring 
      disabled:opacity-50 disabled:pointer-events-none ${variantClasses[variant]} ${sizeClasses[size]} ${className}`}
      onClick={onClick}
      disabled={disabled}
    >
      {children}
    </button>
  );
}