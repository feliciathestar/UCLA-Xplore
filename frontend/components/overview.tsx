import { motion } from 'framer-motion';
import Link from 'next/link';

import { MessageIcon, VercelIcon } from './icons';

export const Overview = () => {
  return (
    <motion.div
      key="overview"
      className="max-w-3xl mx-auto mt-16 md:mt-32"
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.98 }}
      transition={{ delay: 0.5 }}
    >
      <div className="rounded-xl gap-6 p-8 flex items-center leading-relaxed text-center max-w-4xl">
        <div className="flex-shrink-0">
          <img src="/images/bruin_filled.png" alt="Bruin icon" className="w-[90px] h-[90px]" />
        </div>
        <div className="flex flex-col">
          <p className="italic text-[50px] font-bold bg-gradient-to-r from-[#5BC2E7] to-[#3A8DBE] text-transparent bg-clip-text">
            Bruin Xplore
          </p>
          <p className="text-lg font-medium bg-gradient-to-r from-[#5BC2E7] to-[#3A8DBE] text-transparent bg-clip-text">
            Plan your campus life with ease.
          </p>
        </div>
      </div>
    </motion.div>
  );
};
