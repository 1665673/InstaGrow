import sys
from . import environments as env


def apply():
    sys.modules['instapy'].InstaPy.unfollow_users.__code__ = unfollow_users_patch.__code__
    sys.modules['instapy'].InstaPy.like_by_locations.__code__ = like_by_locations_patch.__code__
    sys.modules['instapy'].InstaPy.like_by_tags.__code__ = like_by_tags_patch.__code__
    sys.modules['instapy'].InstaPy.comment_by_locations.__code__ = comment_by_locations_patch.__code__
    #
    sys.modules['instapy.like_util'].check_link.__code__ = check_link_patch.__code__
    sys.modules['instapy.like_util'].like_image.__code__ = like_image_patch.__code__
    #
    sys.modules['instapy.unfollow_util'].follow_user.__code__ = follow_user_patch.__code__
    sys.modules['instapy.unfollow_util'].unfollow_user.__code__ = unfollow_user_patch.__code__
    sys.modules['instapy.unfollow_util'].get_following_status.__code__ = get_following_status_patch.__code__
    sys.modules['instapy.unfollow_util'].verify_action.__code__ = verify_action_patch.__code__
    sys.modules['instapy.unfollow_util'].confirm_unfollow.__code__ = confirm_unfollow_patch.__code__


#
#
#
#
#   patches for
#   sys.modules['instapy'].InstaPy
#
#
#
#
def unfollow_users_patch(self,
                         amount=10,
                         customList=(False, [], "all"),
                         InstapyFollowed=(False, "all"),
                         nonFollowers=False,
                         allFollowing=False,
                         style="FIFO",
                         unfollow_after=None,
                         delay_followbackers=0,  # 864000 = 10 days, 0 = don't delay
                         sleep_delay=600):
    """Unfollows (default) 10 users from your following list"""

    if self.aborting:
        return self

    message = "Starting to unfollow users.."
    highlight_print(self.username, message,
                    "feature", "info", self.logger)

    if unfollow_after is not None:
        if not python_version().startswith(('2.7', '3')):
            self.logger.warning(
                "`unfollow_after` parameter is not"
                " available for Python versions below 2.7")
            unfollow_after = None

    self.automatedFollowedPool = set_automated_followed_pool(
        self.username,
        unfollow_after,
        self.logger,
        self.logfolder,
        delay_followbackers)

    try:
        unfollowed = unfollow(self.browser,
                              self.username,
                              amount,
                              customList,
                              InstapyFollowed,
                              nonFollowers,
                              allFollowing,
                              style,
                              self.automatedFollowedPool,
                              self.relationship_data,
                              self.dont_include,
                              self.white_list,
                              sleep_delay,
                              self.jumps,
                              delay_followbackers,
                              self.logger,
                              self.logfolder)
        self.logger.info(
            "--> Total people unfollowed : {}\n".format(unfollowed))
        self.unfollowed += unfollowed

    except Exception as exc:
        if isinstance(exc, RuntimeWarning):
            self.logger.warning(
                u'Warning: {} , stopping unfollow_users'.format(exc))
            return self

        else:
            self.logger.error('Sorry, an error occurred: {}'.format(exc))
            return self

    return self


def like_by_locations_patch(self,
                            locations=None,
                            amount=50,
                            media=None,
                            skip_top_posts=True):
    """Likes (default) 50 images per given locations"""
    if self.aborting:
        return self

    liked_img = 0
    already_liked = 0
    inap_img = 0
    commented = 0
    followed = 0
    not_valid_users = 0

    locations = locations or []
    self.quotient_breach = False

    #
    #
    #   patch
    #   use cached links for reducing hashtag visits
    #
    #
    if not hasattr(self, "cached_like"):
        self.cached_like = {}

    for index, location in enumerate(locations):
        if self.quotient_breach:
            break

        # self.logger.info('Location [{}/{}]'.format(index + 1, len(locations)))
        # self.logger.info('--> {}'.format(location.encode('utf-8')))

        #
        #
        #   patch
        #   refill cached links if out of stock
        #
        #
        try:
            if location not in self.cached_like or len(self.cached_like[location]) == 0:
                self.env.info("no cached links available for ({0}). fetching {1} links from hashtag..."
                              .format(location, amount))
                cache = get_links_for_location(self.browser,
                                               location,
                                               amount,  # amount was set to 2
                                               self.logger,
                                               media,
                                               skip_top_posts)
                random.shuffle(cache)
                self.cached_like[location] = cache

        except NoSuchElementException as exc:
            self.logger.warning(
                "Error occurred while getting images from location: {}  "
                "~maybe too few images exist\n\t{}\n".format(location, str(
                    exc).encode("utf-8")))
            continue

        #
        #   patch
        #   fetch one link from cache
        #
        links = self.cached_like[location][:1]
        self.cached_like[location] = self.cached_like[location][1:]
        self.env.info("consumed 1 location link for ({0}). {1} links left in cache"
                      .format(location, len(self.cached_like[location])))
        #
        #
        for i, link in enumerate(links):
            if self.jumps["consequent"]["likes"] >= self.jumps["limit"][
                "likes"]:
                self.logger.warning(
                    "--> Like quotient reached its peak!\t~leaving "
                    "Like-By-Locations activity\n")
                self.quotient_breach = True
                # reset jump counter after a breach report
                self.jumps["consequent"]["likes"] = 0
                break

            # self.logger.info('[{}/{}]'.format(i + 1, len(links)))
            # self.logger.info(link)

            try:
                inappropriate, user_name, is_video, reason, scope = (
                    check_link(self.browser,
                               link,
                               self.dont_like,
                               self.mandatory_words,
                               self.mandatory_language,
                               self.is_mandatory_character,
                               self.mandatory_character,
                               self.check_character_set,
                               self.ignore_if_contains,
                               self.logger))

                if not inappropriate and self.delimit_liking:
                    self.liking_approved = verify_liking(self.browser,
                                                         self.max_likes,
                                                         self.min_likes,
                                                         self.logger)

                if not inappropriate and self.liking_approved:
                    # validate user
                    validation, details = self.validate_user_call(user_name)

                    if validation is not True:
                        self.logger.info("--> Not a valid user: {}".format(details))
                        not_valid_users += 1
                        continue
                    else:
                        web_address_navigator(self.browser, link)

                    #
                    #
                    #
                    #
                    #
                    like_state, msg = like_image(self.browser,
                                                 user_name,
                                                 self.blacklist,
                                                 self.logger,
                                                 self.logfolder)

                    if like_state is True:
                        liked_img += 1
                        # reset jump counter after a successful like
                        self.jumps["consequent"]["likes"] = 0

                        # checked_img = True
                        # temp_comments = []
                        #
                        # commenting = random.randint(
                        #     0, 100) <= self.comment_percentage
                        # following = random.randint(
                        #     0, 100) <= self.follow_percentage

                        # if self.use_clarifai and (following or commenting):
                        #     try:
                        #         checked_img, temp_comments, clarifai_tags = (self.query_clarifai())
                        #
                        #     except Exception as err:
                        #         self.logger.error(
                        #             'Image check error: {}'.format(err))

                        # # comments
                        # if (self.do_comment and
                        #         user_name not in self.dont_include and
                        #         checked_img and
                        #         commenting):
                        #
                        #     if self.delimit_commenting:
                        #         (self.commenting_approved,
                        #          disapproval_reason) = verify_commenting(
                        #             self.browser,
                        #             self.max_comments,
                        #             self.min_comments,
                        #             self.comments_mandatory_words,
                        #             self.logger)
                        #     if self.commenting_approved:
                        #         # smart commenting
                        #         comments = self.fetch_smart_comments(
                        #             is_video,
                        #             temp_comments)
                        #         if comments:
                        #             comment_state, msg = comment_image(
                        #                 self.browser,
                        #                 user_name,
                        #                 comments,
                        #                 self.blacklist,
                        #                 self.logger,
                        #                 self.logfolder)
                        #             if comment_state is True:
                        #                 commented += 1
                        #
                        #     else:
                        #         self.logger.info(disapproval_reason)
                        #
                        # else:
                        #     self.logger.info('--> Not commented')
                        #     sleep(1)

                        # # following
                        # if (self.do_follow and
                        #         user_name not in self.dont_include and
                        #         checked_img and
                        #         following and
                        #         not follow_restriction("read", user_name,
                        #                                self.follow_times,
                        #                                self.logger)):
                        #
                        #     follow_state, msg = follow_user(self.browser,
                        #                                     "post",
                        #                                     self.username,
                        #                                     user_name,
                        #                                     None,
                        #                                     self.blacklist,
                        #                                     self.logger,
                        #                                     self.logfolder)
                        #     if follow_state is True:
                        #         followed += 1
                        #
                        # else:
                        #     self.logger.info('--> Not following')
                        #     sleep(1)

                    elif msg == "already liked":
                        already_liked += 1

                    elif msg == "jumped":
                        # will break the loop after certain consecutive
                        # jumps
                        self.jumps["consequent"]["likes"] += 1
                    #
                    #
                    #
                    #
                    #
                    #
                    #
                    #
                    #
                    #

                    else:
                        self.logger.info('--> Image not liked: {}'.format(reason.encode('utf-8')))
                        inap_img += 1

            except NoSuchElementException as err:
                self.logger.error('Invalid Page: {}'.format(err))
        #
        #
        #
        #
        #
        #
        #
        #
        #
        #

    # self.logger.info('Location: {}'.format(location.encode('utf-8')))
    self.logger.info('Liked: {}'.format(liked_img))
    self.logger.info('Already Liked: {}'.format(already_liked))
    # self.logger.info('Commented: {}'.format(commented))
    # self.logger.info('Followed: {}'.format(followed))
    # self.logger.info('Inappropriate: {}'.format(inap_img))
    # self.logger.info('Not valid users: {}\n'.format(not_valid_users))

    self.like_img_success = (liked_img > 0)
    self.followed += followed
    self.liked_img += liked_img
    self.already_liked += already_liked
    self.commented += commented
    self.inap_img += inap_img
    self.not_valid_users += not_valid_users

    return self


def like_by_tags_patch(self,
                       tags=None,
                       amount=50,
                       skip_top_posts=True,
                       use_smart_hashtags=False,
                       use_smart_location_hashtags=False,
                       interact=False,
                       randomize=False,
                       media=None):
    """Likes (default) 50 images per given tag"""
    if self.aborting:
        return self

    liked_img = 0
    already_liked = 0
    inap_img = 0
    commented = 0
    followed = 0
    not_valid_users = 0

    # if smart hashtag is enabled
    if use_smart_hashtags is True and self.smart_hashtags is not []:
        # self.logger.info('Using smart hashtags')
        tags = self.smart_hashtags
    elif use_smart_location_hashtags is True and self.smart_location_hashtags is not []:
        # self.logger.info('Using smart location hashtags')
        tags = self.smart_location_hashtags

    # deletes white spaces in tags
    tags = [tag.strip() for tag in tags]
    tags = tags or []
    self.quotient_breach = False

    #
    #
    #   patch
    #   use cached links for reducing hashtag visits
    #
    #
    if not hasattr(self, "cached_like"):
        self.cached_like = {}

    for index, tag in enumerate(tags):
        if self.quotient_breach:
            break

        try:
            #
            #   patch
            #   refill cached links if out of stock
            #
            #
            if tag not in self.cached_like or len(self.cached_like[tag]) == 0:
                self.env.info("no cached links available for ({0}). fetching {1} links from hashtag..."
                              .format(tag, amount))
                cache = get_links_for_tag(self.browser,
                                          tag,
                                          amount,
                                          skip_top_posts,
                                          randomize,
                                          media,
                                          self.logger)
                random.shuffle(cache)
                self.cached_like[tag] = cache

        except NoSuchElementException:
            self.logger.info('Too few images, skipping this tag')
            continue

        #
        #   patch
        #   fetch one tag from cache
        #
        links = self.cached_like[tag][:1]
        self.cached_like[tag] = self.cached_like[tag][1:]
        self.env.info("consumed 1 tag link for ({0}). {1} links left in cache"
                      .format(tag, len(self.cached_like[tag])))
        #
        #
        # self.logger.info('Tag [{}/{}]'.format(index + 1, len(tags)))
        # self.logger.info('--> {}'.format(tag.encode('utf-8')))

        for i, link in enumerate(links):
            if self.jumps["consequent"]["likes"] >= self.jumps["limit"][
                "likes"]:
                self.logger.warning(
                    "--> Like quotient reached its peak!\t~leaving "
                    "Like-By-Tags activity\n")
                self.quotient_breach = True
                # reset jump counter after a breach report
                self.jumps["consequent"]["likes"] = 0
                break

            # self.logger.info('[{}/{}]'.format(i + 1, len(links)))
            # self.logger.info(link)

            # self.browser.get('http://ifconfig.me/ip')
            # self.logger.info(self.browser.page_source)

            try:
                inappropriate, user_name, is_video, reason, scope = (
                    check_link(self.browser,
                               link,
                               self.dont_like,
                               self.mandatory_words,
                               self.mandatory_language,
                               self.is_mandatory_character,
                               self.mandatory_character,
                               self.check_character_set,
                               self.ignore_if_contains,
                               self.logger)
                )

                if not inappropriate and self.delimit_liking:
                    self.liking_approved = verify_liking(self.browser,
                                                         self.max_likes,
                                                         self.min_likes,
                                                         self.logger)

                if not inappropriate and self.liking_approved:
                    # validate user
                    # validation, details = self.validate_user_call(
                    #    user_name)
                    # if validation is not True:
                    #    self.logger.info(details)
                    #    not_valid_users += 1
                    #    continue
                    # else:
                    #    web_address_navigator(self.browser, link)

                    # sleep(2)
                    self.browser.refresh()
                    sleep(2)
                    # try to like
                    like_state, msg = like_image(self.browser,
                                                 user_name,
                                                 self.blacklist,
                                                 self.logger,
                                                 self.logfolder)

                    if like_state is True:
                        liked_img += 1
                        # reset jump counter after a successful like
                        self.jumps["consequent"]["likes"] = 0

                        # checked_img = True
                        # temp_comments = []
                        #
                        # commenting = (random.randint(0, 100) <=
                        #               self.comment_percentage)
                        # following = (random.randint(0, 100) <=
                        #              self.follow_percentage)

                        # if self.use_clarifai and (following or commenting):
                        #     try:
                        #         checked_img, temp_comments, \
                        #         clarifai_tags = (
                        #             self.query_clarifai())
                        #
                        #     except Exception as err:
                        #         self.logger.error(
                        #             'Image check error: {}'.format(err))
                        #
                        # # comments
                        # if (self.do_comment and
                        #         user_name not in self.dont_include and
                        #         checked_img and
                        #         commenting):
                        #
                        #     if self.delimit_commenting:
                        #         (self.commenting_approved,
                        #          disapproval_reason) = verify_commenting(
                        #             self.browser,
                        #             self.max_comments,
                        #             self.min_comments,
                        #             self.comments_mandatory_words,
                        #             self.logger)
                        #     if self.commenting_approved:
                        #         # smart commenting
                        #         comments = self.fetch_smart_comments(
                        #             is_video,
                        #             temp_comments)
                        #         if comments:
                        #             comment_state, msg = comment_image(
                        #                 self.browser,
                        #                 user_name,
                        #                 comments,
                        #                 self.blacklist,
                        #                 self.logger,
                        #                 self.logfolder)
                        #             if comment_state is True:
                        #                 commented += 1
                        #
                        #     else:
                        #         self.logger.info(disapproval_reason)
                        #
                        # else:
                        #     self.logger.info('--> Not commented')
                        #     sleep(1)
                        #
                        # # following
                        # if (self.do_follow and
                        #         user_name not in self.dont_include and
                        #         checked_img and
                        #         following and
                        #         not follow_restriction("read", user_name,
                        #                                self.follow_times,
                        #                                self.logger)):
                        #
                        #     follow_state, msg = follow_user(self.browser,
                        #                                     "post",
                        #                                     self.username,
                        #                                     user_name,
                        #                                     None,
                        #                                     self.blacklist,
                        #                                     self.logger,
                        #                                     self.logfolder)
                        #     if follow_state is True:
                        #         followed += 1
                        # else:
                        #     self.logger.info('--> Not following')
                        #     sleep(1)
                        #
                        # # interactions (if any)
                        # if interact:
                        #     self.logger.info(
                        #         "--> User gonna be interacted: '{}'"
                        #             .format(user_name))
                        #
                        #     # disable revalidating user in like_by_users
                        #     with self.feature_in_feature("like_by_users", False):
                        #         self.like_by_users(user_name,
                        #                            self.user_interact_amount,
                        #                            self.user_interact_random,
                        #                            self.user_interact_media)

                    elif msg == "already liked":
                        already_liked += 1

                    elif msg == "jumped":
                        # will break the loop after certain consecutive
                        # jumps
                        self.jumps["consequent"]["likes"] += 1

                else:
                    self.logger.info(
                        '--> Image not liked: {}'.format(
                            reason.encode('utf-8')))
                    inap_img += 1

            except NoSuchElementException as err:
                self.logger.error('Invalid Page: {}'.format(err))

    # self.logger.info('Tag: {}'.format(tag.encode('utf-8')))
    self.logger.info('Liked: {}'.format(liked_img))
    self.logger.info('Already Liked: {}'.format(already_liked))
    # self.logger.info('Commented: {}'.format(commented))
    # self.logger.info('Followed: {}'.format(followed))
    # self.logger.info('Inappropriate: {}'.format(inap_img))
    # self.logger.info('Not valid users: {}\n'.format(not_valid_users))

    self.like_img_success = (liked_img > 0)
    self.liked_img += liked_img
    self.already_liked += already_liked
    self.commented += commented
    self.followed += followed
    self.inap_img += inap_img
    self.not_valid_users += not_valid_users

    return self


def comment_by_locations_patch(self,
                               locations=None,
                               amount=50,
                               media=None,
                               skip_top_posts=True):
    """Likes (default) 50 images per given locations"""
    if self.aborting:
        return self

    commented = 0
    followed = 0
    inap_img = 0
    not_valid_users = 0

    locations = locations or []
    self.quotient_breach = False

    #
    #
    #   patch
    #   use cached links for reducing hashtag visits
    #
    #
    if not hasattr(self, "cached_comment"):
        self.cached_comment = {}

    for index, location in enumerate(locations):
        if self.quotient_breach:
            break

        # self.logger.info('Location [{}/{}]'.format(index + 1, len(locations)))
        # self.logger.info('--> {}'.format(location.encode('utf-8')))

        try:
            #
            #   patch
            #   refill cached links if out of stock
            #
            #
            if location not in self.cached_comment or len(self.cached_comment[location]) == 0:
                self.env.info("no cached links available for ({0}). fetching {1} links from hashtag..."
                              .format(location, amount))
                cached = get_links_for_location(self.browser,
                                                location,
                                                amount,
                                                self.logger,
                                                media,
                                                skip_top_posts)
                #
                random.shuffle(cached)
                self.cached_comment[location] = cached
                #

        except NoSuchElementException:
            self.logger.warning('Too few images, skipping this location')
            continue

        #
        #   patch
        #   fetch one link from cache
        #
        links = self.cached_comment[location][:1]
        self.cached_comment[location] = self.cached_comment[location][1:]
        self.env.info("consumed 1 location link for ({0}). {1} links left in cache"
                      .format(location, len(self.cached_comment[location])))
        #
        #

        for i, link in enumerate(links):
            if self.jumps["consequent"]["comments"] >= self.jumps["limit"][
                "comments"]:
                self.logger.warning(
                    "--> Comment quotient reached its peak!\t~leaving "
                    "Comment-By-Locations activity\n")
                self.quotient_breach = True
                # reset jump counter after a breach report
                self.jumps["consequent"]["comments"] = 0
                break

            # self.logger.info('[{}/{}]'.format(i + 1, len(links)))
            # self.logger.info(link)

            try:
                inappropriate, user_name, is_video, reason, scope = (
                    check_link(self.browser,
                               link,
                               self.dont_like,
                               self.mandatory_words,
                               self.mandatory_language,
                               self.is_mandatory_character,
                               self.mandatory_character,
                               self.check_character_set,
                               self.ignore_if_contains,
                               self.logger))
                if not inappropriate:
                    # validate user
                    validation, details = self.validate_user_call(
                        user_name)
                    if validation is not True:
                        self.logger.info(details)
                        not_valid_users += 1
                        continue
                    else:
                        web_address_navigator(self.browser, link)

                    # try to comment
                    self.logger.info(
                        "--> Image not liked: Likes are disabled for the "
                        "'Comment-By-Locations' feature")

                    checked_img = True
                    temp_comments = []
                    commenting = random.randint(
                        0, 100) <= self.comment_percentage
                    following = random.randint(
                        0, 100) <= self.follow_percentage

                    if not commenting:
                        self.logger.info(
                            "--> Image not commented: skipping out of "
                            "given comment percentage")
                        continue

                    if self.use_clarifai:
                        try:
                            checked_img, temp_comments, clarifai_tags = (
                                self.query_clarifai())

                        except Exception as err:
                            self.logger.error(
                                'Image check error: {}'.format(err))

                    if (self.do_comment and
                            user_name not in self.dont_include and
                            checked_img):

                        if self.delimit_commenting:
                            (self.commenting_approved,
                             disapproval_reason) = verify_commenting(
                                self.browser,
                                self.max_comments,
                                self.min_comments,
                                self.comments_mandatory_words,
                                self.logger)
                        if self.commenting_approved:
                            # smart commenting
                            comments = self.fetch_smart_comments(is_video,
                                                                 temp_comments)
                            if comments:
                                comment_state, msg = comment_image(
                                    self.browser,
                                    user_name,
                                    comments,
                                    self.blacklist,
                                    self.logger,
                                    self.logfolder)
                                if comment_state is True:
                                    commented += 1
                                    # reset jump counter after a
                                    # successful comment
                                    self.jumps["consequent"][
                                        "comments"] = 0

                                    # try to follow
                                    if (self.do_follow and
                                            user_name not in
                                            self.dont_include and
                                            checked_img and
                                            following and
                                            not follow_restriction("read",
                                                                   user_name,
                                                                   self.follow_times,
                                                                   self.logger)):

                                        follow_state, msg = follow_user(
                                            self.browser,
                                            "post",
                                            self.username,
                                            user_name,
                                            None,
                                            self.blacklist,
                                            self.logger,
                                            self.logfolder)
                                        if follow_state is True:
                                            followed += 1

                                    else:
                                        self.logger.info(
                                            '--> Not following')
                                        sleep(1)

                            elif msg == "jumped":
                                # will break the loop after certain
                                # consecutive jumps
                                self.jumps["consequent"]["comments"] += 1

                        else:
                            self.logger.info(disapproval_reason)

                    else:
                        self.logger.info('--> Not commented')
                        sleep(1)

                else:
                    self.logger.info(
                        '--> Image not commented: {}'.format(
                            reason.encode('utf-8')))
                    inap_img += 1

            except NoSuchElementException as err:
                self.logger.error('Invalid Page: {}'.format(err))

    self.comment_img_success = (commented > 0)
    # self.logger.info('Location: {}'.format(location.encode('utf-8')))
    self.logger.info('Commented: {}'.format(commented))
    # self.logger.info('Followed: {}'.format(followed))
    # self.logger.info('Inappropriate: {}'.format(inap_img))
    # self.logger.info('Not valid users: {}\n'.format(not_valid_users))

    self.followed += followed
    self.not_valid_users += not_valid_users

    return self


#
#
#
#
#
#   patched for module like_util.py
#
#
#
#
#
#
#
#
def check_link(browser, post_link, dont_like, mandatory_words,
               mandatory_language, mandatory_character,
               is_mandatory_character, check_character_set, ignore_if_contains,
               logger):
    """
    Check the given link if it is appropriate

    :param browser: The selenium webdriver instance
    :param post_link:
    :param dont_like: hashtags of inappropriate phrases
    :param mandatory_words: words of appropriate phrases
    :param ignore_if_contains:
    :param logger: the logger instance
    :return: tuple of
        boolean: True if inappropriate,
        string: the username,
        boolean: True if it is video media,
        string: the message if inappropriate else 'None',
        string: set the scope of the return value
    """

    # Check URL of the webpage, if it already is post's page, then do not
    # navigate to it again
    web_address_navigator(browser, post_link)

    """Check if the Post is Valid/Exists"""
    try:
        post_page = browser.execute_script(
            "return window._sharedData.entry_data.PostPage")

    except WebDriverException:  # handle the possible `entry_data` error
        try:
            browser.execute_script("location.reload()")
            update_activity()

            post_page = browser.execute_script(
                "return window._sharedData.entry_data.PostPage")

        except WebDriverException:
            post_page = None

    if post_page is None:
        logger.warning(
            'Unavailable Page: {}'.format(post_link.encode('utf-8')))
        return True, None, None, 'Unavailable Page', "Failure"

    """Gets the description of the post's link and checks for the dont_like
    tags"""
    graphql = 'graphql' in post_page[0]
    if graphql:
        media = post_page[0]['graphql']['shortcode_media']
        is_video = media['is_video']
        user_name = media['owner']['username']
        image_text = media['edge_media_to_caption']['edges']
        image_text = image_text[0]['node']['text'] if image_text else None
        location = media['location']
        location_name = location['name'] if location else None
        media_edge_string = get_media_edge_comment_string(media)
        # double {{ allows us to call .format here:
        owner_comments = browser.execute_script('''
            latest_comments = window._sharedData.entry_data.PostPage[
            0].graphql.shortcode_media.{}.edges;
            if (latest_comments === undefined) {{
                latest_comments = Array();
                owner_comments = latest_comments
                    .filter(item => item.node.owner.username == arguments[0])
                    .map(item => item.node.text)
                    .reduce((item, total) => item + '\\n' + total, '');
                return owner_comments;}}
            else {{
                return null;}}
        '''.format(media_edge_string), user_name)

    else:
        media = post_page[0]['media']
        is_video = media['is_video']
        user_name = media['owner']['username']
        image_text = media['caption']
        owner_comments = browser.execute_script('''
            latest_comments = window._sharedData.entry_data.PostPage[
            0].media.comments.nodes;
            if (latest_comments === undefined) {
                latest_comments = Array();
                owner_comments = latest_comments
                    .filter(item => item.user.username == arguments[0])
                    .map(item => item.text)
                    .reduce((item, total) => item + '\\n' + total, '');
                return owner_comments;}
            else {
                return null;}
        ''', user_name)

    if owner_comments == '':
        owner_comments = None

    """Append owner comments to description as it might contain further tags"""
    if image_text is None:
        image_text = owner_comments

    elif owner_comments:
        image_text = image_text + '\n' + owner_comments

    """If the image still has no description gets the first comment"""
    if image_text is None:
        if graphql:
            media_edge_string = get_media_edge_comment_string(media)
            image_text = media[media_edge_string]['edges']
            image_text = image_text[0]['node']['text'] if image_text else None

        else:
            image_text = media['comments']['nodes']
            image_text = image_text[0]['text'] if image_text else None

    if image_text is None:
        image_text = "No description"

    logger.info('Image from: {}'.format(user_name.encode('utf-8')))
    logger.info('Link: {}'.format(post_link.encode('utf-8')))
    # logger.info('Description: {}'.format(image_text.encode('utf-8')))

    """Check if mandatory character set, before adding the location to the
    text"""
    if mandatory_language:
        if not check_character_set(image_text):
            return True, user_name, is_video, 'Mandatory language not ' \
                                              'fulfilled', "Not mandatory " \
                                                           "language"

    """Append location to image_text so we can search through both in one
    go."""
    if location_name:
        # logger.info('Location: {}'.format(location_name.encode('utf-8')))
        image_text = image_text + '\n' + location_name

    if mandatory_words:
        if not any((word in image_text for word in mandatory_words)):
            return True, user_name, is_video, 'Mandatory words not ' \
                                              'fulfilled', "Not mandatory " \
                                                           "likes"

    image_text_lower = [x.lower() for x in image_text]
    ignore_if_contains_lower = [x.lower() for x in ignore_if_contains]
    if any((word in image_text_lower for word in ignore_if_contains_lower)):
        return False, user_name, is_video, 'None', "Pass"

    dont_like_regex = []

    for dont_likes in dont_like:
        if dont_likes.startswith("#"):
            dont_like_regex.append(dont_likes + "([^\d\w]|$)")
        elif dont_likes.startswith("["):
            dont_like_regex.append("#" + dont_likes[1:] + "[\d\w]+([^\d\w]|$)")
        elif dont_likes.startswith("]"):
            dont_like_regex.append("#[\d\w]+" + dont_likes[1:] + "([^\d\w]|$)")
        else:
            dont_like_regex.append(
                "#[\d\w]*" + dont_likes + "[\d\w]*([^\d\w]|$)")

    for dont_likes_regex in dont_like_regex:
        quash = re.search(dont_likes_regex, image_text, re.IGNORECASE)
        if quash:
            quashed = \
                (((quash.group(0)).split('#')[1]).split(' ')[0]).split('\n')[
                    0].encode(
                    'utf-8')  # dismiss possible space and newlines
            iffy = ((re.split(r'\W+', dont_likes_regex))[
                        3] if dont_likes_regex.endswith(
                '*([^\\d\\w]|$)') else  # 'word' without format
                    (re.split(r'\W+', dont_likes_regex))[
                        1] if dont_likes_regex.endswith(
                        '+([^\\d\\w]|$)') else  # '[word'
                    (re.split(r'\W+', dont_likes_regex))[
                        3] if dont_likes_regex.startswith(
                        '#[\\d\\w]+') else  # ']word'
                    (re.split(r'\W+', dont_likes_regex))[1])  # '#word'
            inapp_unit = 'Inappropriate! ~ contains "{}"'.format(
                quashed if iffy == quashed else
                '" in "'.join([str(iffy), str(quashed)]))
            return True, user_name, is_video, inapp_unit, "Undesired word"

    return False, user_name, is_video, 'None', "Success"


def like_image_patch(browser, username, blacklist, logger, logfolder):
    """Likes the browser opened image"""
    # check action availability
    if quota_supervisor("likes") == "jump":
        return False, "jumped"

    like_xpath = "//section/span/button/span[@aria-label='Like']"
    unlike_xpath = "//section/span/button/span[@aria-label='Unlike']"

    # find first for like element
    like_elem = browser.find_elements_by_xpath(like_xpath)

    if len(like_elem) == 1:
        # sleep real quick right before clicking the element
        sleep(2)
        click_element(browser, like_elem[0])
        # check now we have unlike instead of like
        liked_elem = browser.find_elements_by_xpath(unlike_xpath)

        if len(liked_elem) == 1:
            # logger.info('--> Image Liked!')
            update_activity('likes')

            if blacklist['enabled'] is True:
                action = 'liked'
                add_user_to_blacklist(
                    username, blacklist['campaign'], action, logger, logfolder)

            # get the post-like delay time to sleep
            naply = get_action_delay("like")
            sleep(naply)
            return True, "success"

        else:
            # if like not seceded wait for 2 min
            logger.info('--> Image was not able to get Liked! maybe blocked ?')
            sleep(120)

    else:
        liked_elem = browser.find_elements_by_xpath(unlike_xpath)
        if len(liked_elem) == 1:
            # logger.info('--> Image already liked!')
            return False, "already liked"

    logger.info('--> Invalid Like Element!')

    return False, "invalid element"


#
#
#
#
#
#
#   patches for
#   sys.modules['instapy.unfollow_util']
#
#
#
#
#
#
#

def follow_user_patch(browser, track, login, user_name, button, blacklist, logger, logfolder):
    # go to user's main profile page
    user_link = "https://www.instagram.com/{}/".format(user_name)
    web_address_navigator(browser, user_link)
    logger.info("Arrived: {}".format(user_link))
    # stay 1 second in profile page
    sleep(1)
    #
    #   patch
    #   the follow action is now included inside verify_action()
    #   so, simply call it and see what happens
    #
    follow_state, msg = verify_action(browser, "follow", track, login,
                                      user_name, None, logger,
                                      logfolder)
    if follow_state:
        if msg == "success":
            logger.info("Successfully followed '{}'!".format(user_name.encode("utf-8")))
        else:
            logger.info("Already following '{}'!".format(user_name))
    else:
        logger.info("Action (follow, {}) failed.".format(user_name))

    return follow_state, msg

    # """ Follow a user either from the profile page or post page or dialog
    # box """
    # # list of available tracks to follow in: ["profile", "post" "dialog"]
    #
    # # check action availability
    # # if quota_supervisor("follows") == "jump":
    # #     return False, "jumped"
    #
    # if track in ["profile", "post"]:
    #     if track == "profile":
    #         # check URL of the webpage, if it already is user's profile
    #         # page, then do not navigate to it again
    #         user_link = "https://www.instagram.com/{}/".format(user_name)
    #         web_address_navigator(browser, user_link)
    #
    #     # find out CURRENT following status
    #     following_status, follow_button = get_following_status(browser,
    #                                                            track,
    #                                                            login,
    #                                                            user_name,
    #                                                            None,
    #                                                            logger,
    #                                                            logfolder)
    #     if following_status in ["Follow", "Follow Back"]:
    #         #
    #         #
    #         #   patch
    #         #   logic refined:
    #         #
    #         #   do not perform follow/unfollow here,
    #         #   function verify_action() will use a loop to do both performing and verifying
    #         #
    #         #
    #         # click_visibly(browser, follow_button)  # click to follow
    #         # sleep(2)
    #         follow_state, msg = verify_action(browser, "follow", track, login,
    #                                           user_name, None, logger,
    #                                           logfolder)
    #         if follow_state is not True:
    #             return False, msg
    #
    #     elif following_status in ["Following", "Requested"]:
    #         if following_status == "Following":
    #             logger.info("--> Already following '{}'!\n".format(user_name))
    #
    #         elif following_status == "Requested":
    #             logger.info("--> Already requested '{}' to follow!\n".format(
    #                 user_name))
    #
    #         # sleep(1)
    #         return False, "already followed"
    #
    #     elif following_status in ["Unblock", "UNAVAILABLE"]:
    #         if following_status == "Unblock":
    #             failure_msg = "user is in block"
    #
    #         elif following_status == "UNAVAILABLE":
    #             failure_msg = "user is inaccessible"
    #
    #         logger.warning(
    #             "--> Couldn't follow '{}'!\t~{}".format(user_name,
    #                                                     failure_msg))
    #         return False, following_status
    #
    #     elif following_status is None:
    #         sirens_wailing, emergency_state = emergency_exit(browser, login,
    #                                                          logger)
    #         if sirens_wailing is True:
    #             return False, emergency_state
    #
    #         else:
    #             logger.warning(
    #                 "--> Couldn't unfollow '{}'!\t~unexpected failure".format(
    #                     user_name))
    #             return False, "unexpected failure"
    # # elif track == "dialog":
    # #     click_element(browser, button)
    # #     sleep(3)
    #
    # # general tasks after a successful follow
    # logger.info("--> Followed '{}'!".format(user_name.encode("utf-8")))
    # update_activity('follows')
    #
    # # # get user ID to record alongside username
    # # user_id = get_user_id(browser, track, user_name, logger)
    # #
    # # logtime = datetime.now().strftime('%Y-%m-%d %H:%M')
    # # log_followed_pool(login, user_name, logger, logfolder, logtime, user_id)
    # #
    # # follow_restriction("write", user_name, None, logger)
    # #
    # # if blacklist['enabled'] is True:
    # #     action = 'followed'
    # #     add_user_to_blacklist(user_name,
    # #                           blacklist['campaign'],
    # #                           action,
    # #                           logger,
    # #                           logfolder)
    # #
    # # # get the post-follow delay time to sleep
    # # naply = get_action_delay("follow")
    # # sleep(naply)
    #
    # return True, "success"


def unfollow_user_patch(browser, track, username, person, person_id, button, relationship_data, logger, logfolder):
    # go to user's main profile page
    user_link = "https://www.instagram.com/{}/".format(person)
    web_address_navigator(browser, user_link)
    logger.info("Arrived: {}".format(user_link))
    # stay 1 second in profile page
    sleep(1)
    #
    #   patch
    #   the follow action is now included inside verify_action()
    #   so, simply call it and see what happens
    #
    follow_state, msg = verify_action(browser, "unfollow", track, username,
                                      person, None, logger,
                                      logfolder)
    if follow_state:
        if msg == "success":
            logger.info("Successfully un-followed '{}'!".format(person.encode("utf-8")))
        else:
            logger.info("Already un-following '{}'!".format(person))
    else:
        logger.info("Action (un-follow, {}) failed.".format(person))

    return follow_state, msg

    # """ Unfollow a user either from the profile or post page or dialog box """
    # # list of available tracks to unfollow in: ["profile", "post" "dialog"]
    #
    # # check action availability
    # # if quota_supervisor("unfollows") == "jump":
    # #     return False, "jumped"
    #
    # if track in ["profile", "post"]:
    #     """ Method of unfollowing from a user's profile page or post page """
    #     if track == "profile":
    #         user_link = "https://www.instagram.com/{}/".format(person)
    #         web_address_navigator(browser, user_link)
    #
    #     # find out CURRENT follow status
    #     following_status, follow_button = get_following_status(browser,
    #                                                            track,
    #                                                            username,
    #                                                            person,
    #                                                            person_id,
    #                                                            logger,
    #                                                            logfolder)
    #
    #     if following_status in ["Following", "Requested"]:
    #         #
    #         #
    #         #   patch
    #         #   logic refined:
    #         #
    #         #   do not perform follow/unfollow here,
    #         #   function verify_action() will use a loop to do both performing and verifying
    #         #
    #         #
    #         # click_visibly(browser, follow_button)  # click to unfollow
    #         # sleep(4)  # TODO: use explicit wait here
    #         # confirm_unfollow(browser, logger)
    #         #
    #         #
    #         unfollow_state, msg = verify_action(browser, "unfollow", track,
    #                                             username,
    #                                             person, person_id, logger,
    #                                             logfolder)
    #         if unfollow_state is not True:
    #             return False, msg
    #
    #     elif following_status in ["Follow", "Follow Back"]:
    #         logger.info(
    #             "--> Already unfollowed '{}'! or a private user that "
    #             "rejected your req".format(
    #                 person))
    #         # post_unfollow_cleanup(["successful", "uncertain"], username,
    #         #                       person, relationship_data, person_id, logger,
    #         #                       logfolder)
    #         return False, "already unfollowed"
    #
    #     elif following_status in ["Unblock", "UNAVAILABLE"]:
    #         if following_status == "Unblock":
    #             failure_msg = "user is in block"
    #
    #         elif following_status == "UNAVAILABLE":
    #             failure_msg = "user is inaccessible"
    #
    #         logger.warning("--> Couldn't unfollow '{}'!\t~{}".format(person, failure_msg))
    #         # post_unfollow_cleanup("uncertain", username, person,
    #         #                       relationship_data, person_id, logger,
    #         #                       logfolder)
    #         return False, following_status
    #
    #     elif following_status is None:
    #         #
    #         #   patch
    #         #   never exit
    #         #
    #         # sirens_wailing, emergency_state = emergency_exit(browser, username, logger)
    #
    #         if sirens_wailing is True:
    #             return False, emergency_state
    #
    #         else:
    #             logger.warning("--> Couldn't unfollow '{}'!\t~unexpected failure".format(person))
    #             return False, "unexpected failure"
    # # elif track == "dialog":
    # #     """  Method of unfollowing from a dialog box """
    # #     click_element(browser, button)
    # #     sleep(4)  # TODO: use explicit wait here
    # #     confirm_unfollow(browser)
    #
    # # general tasks after a successful unfollow
    # logger.info("--> Unfollowed '{}'!".format(person))
    # update_activity('unfollows')
    # post_unfollow_cleanup("successful", username, person, relationship_data,
    #                       person_id, logger, logfolder)
    #
    # # get the post-unfollow delay time to sleep
    # # naply = get_action_delay("unfollow")
    # # sleep(naply)
    #
    # return True, "success"


def get_following_status_patch(browser, track, username, person, person_id, logger,
                               logfolder):
    """ Verify if you are following the user in the loaded page """
    # print("get_following_status_patch")

    if person == username:
        return "OWNER", None

    # if track == "profile":
    #     ig_homepage = "https://www.instagram.com/"
    #     web_address_navigator(browser, ig_homepage + person)

    follow_button_XP = ("//button[text()='Following' or \
                                  text()='Requested' or \
                                  text()='Follow' or \
                                  text()='Follow Back' or \
                                  text()='Unblock']"
                        )
    failure_msg = "--> Unable to detect the following status of '{}'!"
    user_inaccessible_msg = (
        "Couldn't access the profile page of '{}'!\t~might have changed the"
        " username".format(person))

    # check if the page is available
    valid_page = is_page_available(browser, logger)
    if not valid_page:
        return "UNAVAILABLE", None
        # logger.warning(user_inaccessible_msg)
        # person_new = verify_username_by_id(browser,
        #                                    username,
        #                                    person,
        #                                    None,
        #                                    logger,
        #                                    logfolder)
        # if person_new:
        #     web_address_navigator(browser, ig_homepage + person_new)
        #     valid_page = is_page_available(browser, logger)
        #     if not valid_page:
        #         logger.error(failure_msg.format(person_new.encode("utf-8")))
        #         return "UNAVAILABLE", None
        #
        # else:
        #     logger.error(failure_msg.format(person.encode("utf-8")))
        #     return "UNAVAILABLE", None

    # wait until the follow button is located and visible, then get it
    follow_button = explicit_wait(browser, "VOEL", [follow_button_XP, "XPath"],
                                  logger, 7, False)
    if not follow_button:
        browser.execute_script("location.reload()")
        update_activity()

        follow_button = explicit_wait(browser, "VOEL",
                                      [follow_button_XP, "XPath"], logger, 14,
                                      False)
        if not follow_button:
            # cannot find the any of the expected buttons
            logger.error(failure_msg.format(person.encode("utf-8")))
            return None, None

    # get follow status
    following_status = follow_button.text

    return following_status, follow_button


def verify_action_patch(browser, action, track, username, person, person_id, logger,
                        logfolder):
    # print("verify_action_patch")
    #
    #
    #
    #   patch
    #   this function now includes the logic for performing the action itself,
    #   i.e.
    #   it's:  (1) doing an action(follow/unfollow), then verify it
    #          (2) if failed, retry it up to 3 times (4 loop runs including the initial status check)
    #
    #
    #
    #
    #

    """ Verify if the action has succeeded """
    # currently supported actions are follow & unfollow

    if action in ["follow", "unfollow"]:

        # assuming button_change testing is relevant to those actions only
        button_change = False

        if action == "follow":
            post_action_text_correct = ["Following", "Requested"]
            post_action_text_fail = ["Follow", "Follow Back", "Unblock"]

        elif action == "unfollow":
            post_action_text_correct = ["Follow", "Follow Back", "Unblock"]
            post_action_text_fail = ["Following", "Requested"]

        attempt_count = 0
        while True:
            #
            #
            #   patch
            #   refined logic
            #
            #
            if attempt_count > 3:
                logger.warning("Phew! action ({0}, {1}) is not verified.".format(action, username))
                return False, "temporary block"

            #
            #   patch
            #   refined logic
            #

            # for initial follow/unfollow status check, let it pass
            if attempt_count == 0:
                pass
            # for the first action attempt, wait 3 seconds for results
            elif attempt_count == 1:
                sleep(3)
            # for additional attempts, which means we failed the first 1,
            # do reload_page for a more prudent procedure
            else:
                reload_webpage(browser)
                explicit_wait(browser, "PFL", [], logger, 5)

            # find out CURRENT follow status (this is safe as the follow button is before others)
            following_status, follow_button = get_following_status(browser,
                                                                   track,
                                                                   username,
                                                                   person,
                                                                   person_id,
                                                                   logger,
                                                                   logfolder)
            if following_status in post_action_text_correct:
                verified = True
            elif following_status in post_action_text_fail:
                verified = False
            else:
                logger.error("Hey! Action {} is not verified out of an unexpected failure!".format(action))
                return False, "unexpected"

            #
            #   a True value of button_change indicates a verified action
            #   if verified, break the loop
            #
            if verified:
                break

            #
            #   if we get to here, then action is not verified,
            #   perform it or try it one more time
            #
            click_visibly(browser, follow_button)
            if action == "unfollow":
                confirm_unfollow(browser, logger)

            # increase retry-count
            attempt_count += 1

            # elif retry_count == 3:
            #     logger.warning("Phew! Last {0} is not verified."
            #                    "\t~'{1}' might be temporarily blocked "
            #                    "from {0}ing\n"
            #                    .format(action, username))
            #     sleep(210)
            #     return False, "temporary block"

        #
        #
        #
        # if retry_count <= 3:
        #     logger.info("Last {} is verified after reloading the page!".format(action))

    if attempt_count == 0:
        return True, "no-change"
    else:
        return True, "success"


def confirm_unfollow_patch(browser, logger):
    """ Deal with the confirmation dialog boxes during an unfollow """

    #
    #   patch
    #   use an explicit wait to locate "confirm unfollow" button
    #   if it shows up, click it,
    #   if it doesn't, that's it, simply quit. no need to try, it just won't work
    #
    button_selector = "//button[text()='Unfollow']"
    try:
        button = explicit_wait(browser, "VOEL", [button_selector, "XPath"], logger, 15, False)
        #
        #   wait a bit before clicking
        #
        sleep(1)
        click_element(browser, button)
    except Exception as e:
        pass

    # attempt = 0
    #
    # while attempt < 3:
    #     try:
    #         attempt += 1
    #         button_xp = "//button[text()='Unfollow']"  # "//button[contains(
    #         # text(), 'Unfollow')]"
    #         unfollow_button = browser.find_element_by_xpath(button_xp)
    #
    #         if unfollow_button.is_displayed():
    #             click_element(browser, unfollow_button)
    #             sleep(2)
    #             break
    #
    #     except (ElementNotVisibleException, NoSuchElementException) as exc:
    #         # prob confirm dialog didn't pop up
    #         if isinstance(exc, ElementNotVisibleException):
    #             break
    #
    #         elif isinstance(exc, NoSuchElementException):
    #             sleep(1)
    #             pass
