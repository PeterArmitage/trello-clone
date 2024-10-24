import React from 'react';
import { motion } from 'framer-motion';
import { Button } from '../../../common/Button/Button';

interface BoardCardProps {
  title: string;
  description?: string;
  onEdit?: () => void;
  onDelete?: () => void;
  onClick?: () => void;
}

export const BoardCard: React.FC<BoardCardProps> = ({
  title,
  description,
  onEdit,
  onDelete,
  onClick,
}) => {
  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 cursor-pointer"
      onClick={onClick}
    >
      <div className="flex justify-between items-start">
        <div>
          <h3 className="text-xl font-semibold mb-2">{title}</h3>
          {description && <p className="text-gray-600 dark:text-gray-300 text-sm">{description}</p>}
        </div>
        <div className="flex space-x-2">
          {onEdit && (
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                onEdit();
              }}
            >
              Edit
            </Button>
          )}
          {onDelete && (
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                onDelete();
              }}
            >
              Delete
            </Button>
          )}
        </div>
      </div>
    </motion.div>
  );
};
