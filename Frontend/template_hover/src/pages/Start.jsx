import React from 'react';
import Link from 'next/link';
import { FiArrowRight } from "react-icons/fi";
import { MaxWidthWrapper } from "@/components/utils/MaxWidthWrapper";
import { motion } from "framer-motion";
import { SplashButton } from "@/components/buttons/SplashButton";
import { GhostButton } from "@/components/buttons/GhostButton";
import { GlowingChip } from "@/components/utils/GlowingChip";
import { useRouter } from 'next/router';

const Start = () => {
  const router = useRouter();
  return (
    <MaxWidthWrapper className="relative z-20 flex flex-col items-center justify-center pb-12 pt-24 md:pb-36 md:pt-36">
      <motion.div
        initial={{
          y: 25,
          opacity: 0,
        }}
        animate={{
          y: 0,
          opacity: 1,
        }}
        transition={{
          duration: 1.25,
          ease: "easeInOut",
        }}
        className="relative mb-6"
      >
        <GlowingChip>Welcome to Start Page 🚀</GlowingChip>
      </motion.div>
      <motion.h1
        initial={{
          y: 25,
          opacity: 0,
        }}
        animate={{
          y: 0,
          opacity: 1,
        }}
        transition={{
          duration: 1.25,
          delay: 0.25,
          ease: "easeInOut",
        }}
        className="mb-3 text-center text-4xl font-extrabold leading-tight text-zinc-50 sm:text-5xl sm:leading-tight md:text-6xl md:leading-tight lg:text-7xl lg:leading-tight"
      >
        Get Started with Your New Journey
      </motion.h1>
      <motion.p
        initial={{
          y: 25,
          opacity: 0,
        }}
        animate={{
          y: 0,
          opacity: 1,
        }}
        transition={{
          duration: 1.25,
          delay: 0.5,
          ease: "easeInOut",
        }}
        className="mb-9 max-w-2xl text-center text-lg text-zinc-400 sm:text-xl md:text-2xl"
      >
        Explore the features, benefits, and possibilities of our platform. Let's create something amazing together.
      </motion.p>
      <motion.div
        initial={{
          y: 25,
          opacity: 0,
        }}
        animate={{
          y: 0,
          opacity: 1,
        }}
        transition={{
          duration: 1.25,
          delay: 0.75,
          ease: "easeInOut",
        }}
        className="flex flex-col items-center gap-4 sm:flex-row"
      >
        <Link href="/start" passHref>
          <SplashButton className="flex items-center gap-2 px-6 py-3 text-xl font-semibold text-white bg-green-600 rounded-lg shadow-lg hover:bg-green-700">
            Get Started
            <FiArrowRight />
          </SplashButton>
        </Link>
        <GhostButton
          onClick={() => router.push("/learn-more")}
          className="flex items-center gap-2 px-6 py-3 text-xl font-semibold text-green-600 bg-white border-2 border-green-600 rounded-lg shadow-lg hover:bg-green-100"
        >
          Learn More
        </GhostButton>
      </motion.div>
      <div className="mt-12 grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-3">
        <FeatureCard
          icon={<FiArrowRight size={30} />}
          title="Feature One"
          description="Detailed description of feature one."
        />
        <FeatureCard
          icon={<FiArrowRight size={30} />}
          title="Feature Two"
          description="Detailed description of feature two."
        />
        <FeatureCard
          icon={<FiArrowRight size={30} />}
          title="Feature Three"
          description="Detailed description of feature three."
        />
      </div>
    </MaxWidthWrapper>
  );
};

const FeatureCard = ({ icon, title, description }) => (
  <div className="p-6 bg-white rounded-lg shadow-md">
    <div className="flex items-center justify-center w-12 h-12 mb-4 bg-green-100 rounded-full">
      {icon}
    </div>
    <h3 className="mb-2 text-2xl font-bold text-zinc-800">{title}</h3>
    <p className="text-zinc-600">{description}</p>
  </div>
);

export default Start;
