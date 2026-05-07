import { ReactNode } from "react";

interface CardProps {
  children: ReactNode;
  className?: string;
}

export default function Card({ children, className = "" }: CardProps) {
  return (
    <div className={`glass rounded-2xl p-6 shadow-lg ${className}`}>
      {children}
    </div>
  );
}
